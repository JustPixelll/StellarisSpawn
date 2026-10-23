"""Execute the actual mod scripts in a small, explicitly limited graph model.
This is NOT Stellaris or an engine compatibility test.
"""
from pathlib import Path
from dataclasses import dataclass, field
import re, math, random, hashlib, json, zipfile, sys
from collections import deque

BASE = Path(__file__).resolve().parent.parent
PACK = Path(sys.argv[1]).resolve() if len(sys.argv)>1 else BASE
MOD = PACK / 'niki_starburst_tail_start'

TOKEN = re.compile(r'\s+|#[^\n]*|"(?:\\.|[^"\\])*"|>=|<=|!=|[{}=<>]|[^\s{}=<>#"]+')

def parse(text):
    tokens = [m.group() for m in TOKEN.finditer(text)
              if not m.group().isspace() and not m.group().startswith('#')]
    def block(i, nested=False):
        out=[]
        while i < len(tokens):
            if tokens[i] == '}':
                assert nested, 'Unexpected closing brace'
                return out, i+1
            key=tokens[i]; i+=1
            if i == len(tokens) or tokens[i] not in ('=','>','<','>=','<=','!='):
                out.append((key, None, None)); continue
            op=tokens[i]; i+=1
            assert i<len(tokens), f'Missing value for {key}'
            if tokens[i]=='{': value,i=block(i+1, True)
            else: value=tokens[i].strip('"'); i+=1
            out.append((key,op,value))
        assert not nested, 'Unclosed block'
        return out,i
    return block(0)[0]

def get(block,key,default=None):
    return next((v for k,o,v in block if k==key),default)

effects={}
for p in (MOD/'common/scripted_effects').glob('*.txt'):
    for k,o,v in parse(p.read_text()): effects[k]=v
triggers={}
for p in (MOD/'common/scripted_triggers').glob('*.txt'):
    for k,o,v in parse(p.read_text()): triggers[k]=v
events={}
for p in (MOD/'events').glob('*.txt'):
    for k,o,v in parse(p.read_text()):
        if k=='country_event': events[get(v,'id')]=v

@dataclass(eq=False)
class Obj:
    id: str
    x: float=0
    y: float=0
    flags: set=field(default_factory=set)
    vars: dict=field(default_factory=dict)
    owner: object=None
    hostile_to: set=field(default_factory=set)
    aura: bool=False
    fleets: list=field(default_factory=list)
    planets: list=field(default_factory=list)

@dataclass
class Ctx:
    scope: Obj
    prev: object
    root: Obj

class Model:
    def __init__(self, stars, edges, home, fail=None, nomad=False,
                 origin='origin_default', galaxy_radius=500, fail_radius=False):
        self.stars=stars
        self.edges={frozenset(e) for e in edges}
        self.player=Obj('player')
        self.player.origin=origin
        self.player.nomad=nomad
        self.home=home
        self.home.owner=self.player
        self.targets={}
        self.messages=[]
        self.pending=[]
        self.fail=fail
        self.galaxy_radius=galaxy_radius
        self.fail_radius=fail_radius
        self.move_count=0
        self.rng=random.Random(9)
        self.day=1
        self.executed=0
        self._adj_edges=None
        self._adj={}

    def child(self,o,c): return Ctx(o,c.scope,c.root)
    def ref(self,v,c):
        if v.lower()=='this': return c.scope
        if v.lower()=='prev': return c.prev
        if v.lower()=='root': return c.root
        if v=='capital_scope': return self.home
        if v=='solar_system': return c.scope
        if v=='owner': return c.scope.owner
        if v.startswith('event_target:'): return self.targets.get(v.split(':',1)[1])
        raise ValueError('Unknown ref '+v)

    def flag(self,v,c):
        if '@' in v:
            a,b=v.split('@'); return a+'@'+self.ref(b,c).id
        return v

    def number(self,v,c):
        if v=='trigger:distance_to_core_percent':
            # 4.5.2 exports a fraction, confirmed in the submitted save.
            return math.hypot(c.scope.x,c.scope.y)/self.galaxy_radius
        try: return float(v)
        except ValueError:
            if '.' in v:
                scope,key=v.rsplit('.',1)
                return self.ref(scope,c).vars.get(key,0)
            return c.scope.vars.get(v,0)

    def objects(self,k,c):
        if k.endswith('neighbor_system'):
            if self._adj_edges is not self.edges:
                self._adj={s:[] for s in self.stars}
                for edge in self.edges:
                    a,b=tuple(edge)
                    self._adj[a].append(b); self._adj[b].append(a)
                self._adj_edges=self.edges
            return list(self._adj.get(c.scope, []))
        if k.endswith('system_planet'): return c.scope.planets
        if k.endswith('fleet_in_system'): return c.scope.fleets
        if k.endswith('system'): return list(self.stars)
        raise ValueError(k)

    def compare(self,a,op,b):
        return {'=':a==b,'!=':a!=b,'>':a>b,'<':a<b,'>=':a>=b,'<=':a<=b}[op]

    def condition(self,b,c,mode='AND'):
        values=(self.cond(k,o,v,c) for k,o,v in b)
        return any(values) if mode=='OR' else all(values)

    def cond(self,k,o,v,c):
        if k in triggers: return self.condition(triggers[k],c)==(v=='yes')
        if k in ('AND','OR'): return self.condition(v,c,k)
        if k=='NOT': return not self.condition(v,c)
        if k.startswith('event_target:') or k in ('root','prev','capital_scope','solar_system','owner'):
            target=self.ref(k,c)
            return bool(target) and self.condition(v,self.child(target,c))
        if k.startswith('any_'):
            return any(self.condition(v,self.child(s,c)) for s in self.objects(k,c))
        if k.startswith('count_'):
            count=sum(self.condition(get(v,'limit',[]),self.child(s,c)) for s in self.objects(k,c))
            rule=next(x for x in v if x[0]=='count')
            return self.compare(count,rule[1],self.number(rule[2],c))
        if k in ('has_star_flag','has_country_flag'): result=self.flag(v,c) in c.scope.flags
        elif k=='has_owner': result=(c.scope.owner is not None)==(v=='yes')
        elif k=='has_psionic_aura': result=c.scope.aura==(v=='yes')
        elif k=='always': result=v=='yes'
        elif k=='exists': result=self.ref(v,c) is not None
        elif k=='is_owned_by': result=c.scope.owner is self.ref(v,c)
        elif k=='is_hostile': result=self.ref(v,c) in c.scope.hostile_to
        elif k=='is_same_value': result=c.scope is self.ref(v,c)
        elif k=='has_hyperlane_to': result=frozenset((c.scope,self.ref(v,c))) in self.edges
        elif k=='distance_to_core_percent':
            result=self.compare(self.number('trigger:distance_to_core_percent',c),o,float(v))
        elif k=='check_variable':
            key=get(v,'which')
            rule=next(x for x in v if x[0]=='value')
            result=self.compare(c.scope.vars.get(key,0),rule[1],self.number(rule[2],c))
        elif k=='distance':
            source=self.ref(get(v,'source'),c)
            dist=math.hypot(c.scope.x-source.x,c.scope.y-source.y)
            result=all(self.compare(dist,op,float(value)) for key,op,value in v
                       if key in ('min_distance','max_distance'))
        elif k=='is_ai': result=(c.scope is not self.player)==(v=='yes')
        elif k=='is_multiplayer': result=v=='no'
        elif k=='galaxy_shape': result=v=='starburst'
        elif k=='days_passed': result=self.compare(self.day,o,float(v))
        elif k=='is_nomadic': result=self.player.nomad==(v=='yes')
        elif k=='has_origin': result=self.player.origin==v
        else: raise ValueError('Unknown trigger: '+k)
        return result

    def run(self,b,c):
        i=0
        while i<len(b):
            k,o,v=b[i]
            self.executed+=1
            assert self.executed<2_000_000, 'Execution bound exceeded'
            if k=='if':
                did=self.condition(get(v,'limit',[]),c)
                if did: self.run([n for n in v if n[0]!='limit'],c)
                if i+1<len(b) and b[i+1][0]=='else':
                    i+=1
                    if not did: self.run(b[i][2],c)
            elif k=='else': raise AssertionError('Orphan else')
            elif k in effects: self.run(effects[k],c)
            elif k.startswith('event_target:') or k in ('root','prev','capital_scope','solar_system'):
                self.run(v,self.child(self.ref(k,c),c))
            elif k.startswith(('every_','random_','ordered_')):
                pool=[s for s in self.objects(k,c)
                      if self.condition(get(v,'limit',[]),self.child(s,c))]
                if k.startswith('ordered_'):
                    pool.sort(key=lambda s:self.number(get(v,'order_by'),self.child(s,c)),
                              reverse=get(v,'inverse','no')!='yes')
                    pool=pool[int(get(v,'position','0')):int(get(v,'position','0'))+1]
                elif k.startswith('random_'): pool=pool[:1]
                body=[n for n in v if n[0] not in ('limit','order_by','inverse','position')]
                for s in pool: self.run(body,self.child(s,c))
            elif k=='while':
                n=0
                while self.condition(get(v,'limit',[]),c):
                    n+=1; assert n<3000
                    self.run([a for a in v if a[0]!='limit'],c)
            elif k=='save_event_target_as': self.targets[v]=c.scope
            elif k.startswith('set_') and k.endswith('_flag'): c.scope.flags.add(self.flag(v,c))
            elif k.startswith('remove_') and k.endswith('_flag'): c.scope.flags.discard(self.flag(v,c))
            elif k in ('set_variable','change_variable','multiply_variable','subtract_variable'):
                key=get(v,'which'); value=self.number(get(v,'value'),c)
                if k=='change_variable': value=c.scope.vars.get(key,0)+value
                elif k=='multiply_variable': value=c.scope.vars.get(key,0)*value
                elif k=='subtract_variable': value=c.scope.vars.get(key,0)-value
                c.scope.vars[key]=value
            elif k=='export_trigger_value_to_variable':
                value=self.number('trigger:'+get(v,'trigger'),c)
                c.scope.vars[get(v,'variable')]=0 if self.fail_radius else value
            elif k=='clear_variable': c.scope.vars.pop(v,None)
            elif k in ('add_hyperlane','remove_hyperlane'):
                a=self.ref(get(v,'from'),c); b2=self.ref(get(v,'to'),c)
                assert a is not b2, 'Self hyperlane'
                edge=frozenset((a,b2))
                if k=='add_hyperlane': self.edges.add(edge)
                else: self.edges.discard(edge)
                self._adj_edges=None
            elif k=='move_system':
                self.move_count+=1
                fail=self.fail=='home' and c.scope is self.home
                fail=fail or (self.fail=='companion' and self.move_count==2)
                if not fail:
                    target=self.ref(get(v,'target'),c)
                    angle=math.atan2(target.y,target.x)
                    if get(v,'direction')=='corewards': angle+=math.pi
                    distance=(float(get(v,'min_distance'))+float(get(v,'max_distance')))/2
                    angle+=self.rng.uniform(-.55,.55)
                    c.scope.x=target.x+math.cos(angle)*distance
                    c.scope.y=target.y+math.sin(angle)*distance
                    # Engine placement/collision/fleet semantics are not emulated.
                    self.edges={e for e in self.edges if c.scope not in e}
            elif k=='country_event':
                if get(v,'days'):
                    self.pending.append((self.day+int(get(v,'days')),get(v,'id')))
                else: self.fire(get(v,'id'))
            elif k in ('log','set_surveyed'): pass
            else: raise ValueError('Unknown effect: '+k)
            i+=1

    def fire(self,event_id):
        c=Ctx(self.player,None,self.player)
        event=events[event_id]
        if self.condition(get(event,'trigger',[]),c):
            if get(event,'hide_window')!='yes': self.messages.append(event_id)
            self.run(get(event,'immediate',[]),c)

    def advance(self,days=1):
        self.day+=days
        due=[item for item in self.pending if item[0]<=self.day]
        self.pending=[item for item in self.pending if item[0]>self.day]
        for _,event_id in due: self.fire(event_id)

    def start(self,verify=True):
        self.fire('ntt.2')
        if verify and self.pending: self.advance()

def reached(stars,edges,start,blocked=frozenset()):
    adjacency={s:set() for s in stars}
    for edge in edges:
        a,b=tuple(edge)
        adjacency[a].add(b); adjacency[b].add(a)
    seen={start}; todo=[start]
    while todo:
        a=todo.pop()
        for b in adjacency[a]:
            if b not in seen and b not in blocked: seen.add(b); todo.append(b)
    return seen

def galaxy(seed=0,pocket=0,arm_length=34,radial_step=13):
    rng=random.Random(seed)
    stars=[Obj('core',40,0)]
    edges=[]
    arms=[]
    for arm in range(6):
        rows=[]
        angle=arm*math.pi/3
        for j in range(1,arm_length+1):
            row=[]
            for lane in range(3):
                radius=30+radial_step*j
                lateral=(lane-1)*18
                s=Obj(f'a{arm}r{j}l{lane}',
                      math.cos(angle)*radius-math.sin(angle)*lateral,
                      math.sin(angle)*radius+math.cos(angle)*lateral)
                stars.append(s); row.append(s)
                if lane: edges.append((row[lane-1],s))
                if j>1: edges.append((rows[-1][lane],s))
                else: edges.append((stars[0],s))
            rows.append(row)
        arms.append(rows)
    home=arms[seed%6][7+seed%3][1]
    # An attached origin-style pocket with its own country/aura.
    previous=home
    for j in range(pocket):
        s=Obj(f'origin{j}',home.x+5*j,home.y+60+14*j,aura=True)
        if j==pocket-1: s.owner=Obj('story_empire')
        stars.append(s); edges.append((previous,s)); previous=s
    # A disconnected, extremely far-away special cluster must not be chosen.
    l1=Obj('unreachable1',650,650); l2=Obj('unreachable2',660,650)
    stars.extend([l1,l2]); edges.append((l1,l2))
    return stars,edges,home

def huge_galaxy(mode):
    """Synthetic 1,000-star Starburst with a small attached story pocket.

    This is a test topology, not Stellaris's generator or the Mindwardens
    origin scripts. Use a nominal radius of 450 map units for these cases.
    """
    stars,edges,home=galaxy(pocket=5,arm_length=55,radial_step=7.45)
    while len(stars)<1000:
        s=Obj('extra'+str(len(stars)),35,len(stars)-998)
        stars.append(s); edges.append((stars[0],s))
    assert len(stars)==1000
    neutral=Obj('neutral')
    foreign=Obj('foreign')
    for s in stars:
        if s.id.startswith('unreachable'): continue
        if mode=='compact': s.x*=.6; s.y*=.6
        if mode=='neutral_fleets': s.fleets=[Obj('visitor',owner=neutral)]
        if s.id.startswith('a'):
            row=int(s.id.split('r')[1].split('l')[0])
            if mode=='outside_band':
                radius=36+4.5*row if row<=47 else 432+2*(row-48)
                angle=math.atan2(s.y,s.x)
                s.x=radius*math.cos(angle); s.y=radius*math.sin(angle)
            if mode=='crowded' and row>=45 and row%3==0: s.owner=foreign
    return stars,edges,home

checks=[]
def record(label): checks.append(label); print('PASS',label)
def cleanup_ok(m):
    assert not any(any(f.startswith('ntt_') for f in s.flags) for s in m.stars)
    assert not any(s.vars for s in m.stars)
    assert all(k.startswith('ntt_diag_') for k in m.player.vars)
    assert 'ntt_growing' not in m.player.flags
    assert 'ntt_bad_layout' not in m.player.flags
    assert 'ntt_bad_verification' not in m.player.flags
    assert 'ntt_pending_verification' not in m.player.flags

# Parse every shipped game script and verify localisations and launcher paths.
for p in MOD.rglob('*.txt'): parse(p.read_text(encoding='utf-8-sig'))
for p in (PACK/'niki_starburst_tail_start.mod', MOD/'descriptor.mod'): parse(p.read_text())
assert 'path="mod/niki_starburst_tail_start"' in (PACK/'niki_starburst_tail_start.mod').read_text()
keys=set()
for p in (MOD/'localisation').rglob('*.yml'):
    assert p.read_bytes().startswith(b'\xef\xbb\xbf')
    contents=p.read_text('utf-8-sig')
    own=re.findall(r'^ ([\w.]+):0 "',contents,re.M)
    assert len(own)==len(set(own))
    if not keys: keys=set(own)
    else: assert keys==set(own)
for event in events.values():
    for k in ('title','desc'):
        if get(event,k): assert get(event,k) in keys
record('Package grammar, UTF-8 BOM localisation, event references and descriptor path')

# Meaningful graph scenarios run the shipped scripted effects, not a second
# implementation of the selection/repair algorithm.
for seed in range(8):
    stars,edges,home=galaxy(seed,pocket=5 if seed%2 else 0)
    m=Model(stars,edges,home)
    original_edges=set(m.edges)
    original_owned={s.id:s.owner for s in stars}
    connected=reached(stars,m.edges,home)
    original_positions={s:(s.x,s.y) for s in stars}
    m.start()
    assert m.messages==['ntt.10'], (seed,m.messages)
    moved={s for s in stars if original_positions[s]!=(s.x,s.y)}
    assert home in moved
    assert 'ntt_complete' in m.player.flags
    assert not {'unreachable1','unreachable2'} & {s.id for s in moved}
    assert reached(stars,m.edges,home)==connected
    internal_before={e for e in original_edges if e<=moved}
    internal_after={e for e in m.edges if e<=moved}
    assert internal_before==internal_after
    crossings=[e for e in m.edges if len(e & moved)==1]
    assert len(crossings)==1 and home in crossings[0]
    assert all(math.dist((a.x,a.y),(b.x,b.y))<=40 for a,b in map(tuple,crossings))
    assert all(original_owned[s.id] is s.owner for s in stars)
    if seed%2:
        assert all(s in moved for s in stars if s.id.startswith('origin'))
    assert all(math.hypot(s.x,s.y)<=500 for s in moved)
    cleanup_ok(m)
    after=(set(m.edges),[(s.x,s.y) for s in stars],list(m.messages))
    m.start()
    assert after==(set(m.edges),[(s.x,s.y) for s in stars],list(m.messages))
record('8 synthetic 615/620-system layouts: outer target, original internal graph, one short exit, preserved connectivity/ownership, origin pocket and idempotence')

# Regressions for the reported Huge Starburst / Mindwardens setup. The pocket
# is structural only: actual Mindwardens event/aura behaviour is not emulated.
for mode in ('compact','neutral_fleets','outside_band','crowded'):
    stars,edges,home=huge_galaxy(mode)
    m=Model(stars,edges,home,origin='origin_mindwardens',galaxy_radius=450)
    before_edges=set(m.edges)
    before_positions={s:(s.x,s.y) for s in stars}
    before_owners={s:s.owner for s in stars}
    connected=reached(stars,m.edges,home)
    if mode in ('compact','outside_band'):
        # Neither layout has a normal star in v0.1.0's fixed radial band.
        assert not any(75 <= math.hypot(s.x,s.y)/4.5 <= 94
                       for s in stars if s.id.startswith('a'))
    m.start()
    assert m.messages==['ntt.10'], (mode,m.messages,m.player.vars)
    tail=m.targets['ntt_tail']
    assert tail.owner is None
    assert not tail.aura and not any(p.owner for p in tail.planets)
    assert not tail.id.startswith('unreachable')
    assert math.hypot(*before_positions[tail])/450 >= .85*m.player.vars['ntt_diag_radius']
    moved={s for s in stars if before_positions[s]!=(s.x,s.y)}
    assert home in moved
    assert all(s in moved for s in stars if s.id.startswith('origin'))
    assert {e for e in before_edges if e<=moved} == {e for e in m.edges if e<=moved}
    assert reached(stars,m.edges,home)==connected
    exits=[e for e in m.edges if len(e & moved)==1]
    assert exits==[frozenset((home,tail))]
    assert math.dist((home.x,home.y),(tail.x,tail.y))<=40
    assert all(math.hypot(s.x,s.y)<=450 for s in moved)
    assert all(s.owner is before_owners[s] for s in stars)
    if mode=='outside_band':
        assert math.hypot(home.x,home.y)<math.hypot(tail.x,tail.y)
    if mode=='neutral_fleets': assert tail.fleets
    if mode=='crowded':
        assert not m.condition(triggers['ntt_tail_has_buffer'],Ctx(tail,None,m.player))
    assert m.player.vars['ntt_diag_main'] >= m.player.vars['ntt_diag_outer'] >= \
        m.player.vars['ntt_diag_empty'] >= m.player.vars['ntt_diag_clear'] >= \
        m.player.vars['ntt_diag_candidates'] > 0
    cleanup_ok(m)
    after=(set(m.edges),[(s.x,s.y) for s in stars],list(m.messages),dict(m.player.vars))
    m.start()
    assert after==(set(m.edges),[(s.x,s.y) for s in stars],list(m.messages),dict(m.player.vars))
record('4 synthetic 1,000-system regressions: compact extent, neutral fleets, endpoints beyond 94%, crowded borders; story pocket, topology, ownership, radius and idempotence checked')

# Exercise rejection gates independently of the graph classifier. An occupied
# or dangerous rim must not make the adaptive band fall back into the core.
for hazard in ('system_owner','planet_owner','hostile_fleet','aura','too_near','radius_export'):
    home=Obj('home',-350,0)
    core=Obj('core',100,0)
    rim=Obj('rim',440,0)
    stars=[home,core,rim]
    m=Model(stars,[(home,core),(core,rim)],home,galaxy_radius=450,
            fail_radius=hazard=='radius_export')
    home.flags.update(('ntt_cluster','ntt_reachable'))
    for s in (core,rim): s.flags.update(('ntt_main','ntt_reachable'))
    m.targets['ntt_home']=home
    foreign=Obj('foreign')
    if hazard=='system_owner': rim.owner=foreign
    if hazard=='planet_owner': rim.planets=[Obj('colony',owner=foreign)]
    if hazard=='hostile_fleet':
        foreign.hostile_to.add(m.player)
        rim.fleets=[Obj('hostile',owner=foreign)]
    if hazard=='aura': rim.aura=True
    if hazard=='too_near': home.x=390
    before=(set(m.edges),[(s.x,s.y) for s in stars])
    c=Ctx(m.player,None,m.player)
    m.run(effects['ntt_select_tail'],c)
    m.run(effects['ntt_cleanup'],c)
    assert m.messages==['ntt.11'], (hazard,m.messages)
    assert before==(set(m.edges),[(s.x,s.y) for s in stars])
    assert m.player.vars['ntt_diag_candidates']==0
    if hazard=='radius_export': assert m.player.vars['ntt_diag_radius']==0
    else: assert m.player.vars['ntt_diag_radius']>0 and m.player.vars['ntt_diag_outer']==1
    if hazard in ('system_owner','planet_owner'): assert m.player.vars['ntt_diag_empty']==0
    if hazard in ('hostile_fleet','aura'):
        assert m.player.vars['ntt_diag_empty']==1 and m.player.vars['ntt_diag_clear']==0
    if hazard=='too_near': assert m.player.vars['ntt_diag_clear']==1
    cleanup_ok(m)
record('6 tail rejection cases retain diagnostics and leave the map unchanged: owners, colonies, hostile fleets, aura, separation and failed numeric export')

stars,edges,home=galaxy()
m=Model(stars,edges,home)
for s in stars:
    if math.hypot(s.x,s.y)>350: s.owner=Obj('foreign')
before=(set(m.edges),[(s.x,s.y) for s in stars])
m.start()
assert m.messages==['ntt.11'],m.messages
assert before==(set(m.edges),[(s.x,s.y) for s in stars])
cleanup_ok(m)
record('No eligible tail: no graph or position changes')

# Psionic auras elsewhere in the main galaxy do not imply a detached origin pocket.
stars,edges,home=galaxy()
stars[0].aura=True
m=Model(stars,edges,home)
m.start()
assert m.messages==['ntt.10'],m.messages
cleanup_ok(m)
record('Unrelated psionic aura in the core component does not block relocation')

stars,edges,home=galaxy(pocket=40)
m=Model(stars,edges,home)
before=(set(m.edges),[(s.x,s.y) for s in stars])
m.start()
assert m.messages==['ntt.12']
assert before==(set(m.edges),[(s.x,s.y) for s in stars])
cleanup_ok(m)
record('Oversized attached branch: no graph or position changes')

for origin,nomad in [('origin_default',True),('origin_common_ground',False),
                     ('origin_hegemon',False),('origin_imperial_vassal',False),
                     ('origin_payback',False),('origin_broken_shackles',False)]:
    stars,edges,home=galaxy()
    m=Model(stars,edges,home,nomad=nomad,origin=origin)
    before=(set(m.edges),[(s.x,s.y) for s in stars])
    m.start()
    assert m.messages==['ntt.12']
    assert before==(set(m.edges),[(s.x,s.y) for s in stars])
record('Nomadic and five linked-empire origin guards')

for failure,message in [('home','ntt.14'),('companion','ntt.13')]:
    stars,edges,home=galaxy()
    m=Model(stars,edges,home,fail=failure)
    m.start()
    assert m.messages==[message],m.messages
    assert 'ntt_failed' in m.player.flags and 'ntt_complete' not in m.player.flags
    cleanup_ok(m)
record('Injected home and companion placement failures produce failure messages, never success')

# A short spoke reaches farther outward than a long arm. Radial ranking
# wrongly picks the spoke; the requested tail requires travel along the graph.
# Compare every computed BFS depth with an independent queue-based reference.
for reverse in (False,True):
    stars,edges,home=galaxy(pocket=5)
    shortcut=Obj('short_outer_spoke',499,0)
    stars.append(shortcut);edges.append((stars[0],shortcut))
    if reverse: stars.reverse()
    m=Model(stars,edges,home)
    old_edges=set(m.edges)
    m.start(verify=False)
    assert not m.messages and 'ntt_complete' not in m.player.flags
    assert 'ntt_pending_verification' in m.player.flags
    assert m.targets['ntt_tail'] is not shortcut
    seeds=[s for s in stars if 'ntt_main' in s.flags and
           s.vars['ntt_radius']<=m.player.vars['ntt_inner_band']]
    depths={s:0 for s in seeds};queue=deque(seeds)
    adjacency={s:set() for s in stars}
    for a,b in map(tuple,old_edges):
        adjacency[a].add(b);adjacency[b].add(a)
    while queue:
        a=queue.popleft()
        for b in adjacency[a]:
            if b not in depths:
                depths[b]=depths[a]+1;queue.append(b)
    for star,depth in depths.items():
        assert star.vars['ntt_depth']==depth, (star.id,depth,star.vars)
    candidates=[s for s in stars if 'ntt_candidate' in s.flags]
    assert m.player.vars['ntt_diag_depth']==max(depths[s] for s in candidates)>20
    m.advance()
    assert m.messages==['ntt.10']
    assert m.player.vars['ntt_diag_exits']==1
    cleanup_ok(m)
record('Deep tail outranks a farther-out short spoke; every BFS depth matches an independent reference in both system iteration orders; success waits for the next-day check')

# Engine evidence: the supplied 4.5.2 save exported 0.99458 for the outermost
# connected main star. A 0-100 model concealed the previous rim-check bug.
probe=Obj('radius_probe',503.60894,0)
m=Model([probe],[],probe,galaxy_radius=506.3525)
value=m.number('trigger:distance_to_core_percent',Ctx(probe,None,m.player))
assert abs(value-0.99458)<0.00001
assert value<1 and value>.95
record('Radius export uses 0-1 units consistent with observed Stellaris 4.5.2 data')

for fault in ('extra_exit','missing_internal_edge','wrong_exit','wrong_position','missing_target'):
    stars,edges,home=galaxy(arm_length=20)
    m=Model(stars,edges,home)
    m.start(verify=False)
    assert not m.messages and 'ntt_complete' not in m.player.flags
    cluster={s for s in stars if 'ntt_cluster' in s.flags}
    tail=m.targets['ntt_tail']
    if fault=='extra_exit':
        outside=next(s for s in stars if s not in cluster and s is not tail)
        m.edges.add(frozenset((home,outside)))
    elif fault=='missing_internal_edge':
        m.edges.remove(next(e for e in m.edges if e<=cluster))
    elif fault=='wrong_exit':
        m.edges.remove(frozenset((home,tail)))
        other=next(s for s in cluster if s is not home)
        m.edges.add(frozenset((other,tail)))
    elif fault=='wrong_position': home.x+=200
    else: del m.targets['ntt_tail']
    m._adj_edges=None
    m.advance()
    assert m.messages==['ntt.15'], (fault,m.messages)
    assert 'ntt_complete' not in m.player.flags and 'ntt_failed' in m.player.flags
    cleanup_ok(m)
record('Five post-move faults are rejected: extra exit, missing internal edge, wrong exit origin, wrong position and missing target')

stars,edges,home=galaxy(pocket=5)
m=Model(stars,edges,home,origin='origin_mindwardens')
m.day=5
m.player.flags.update(('ntt_attempted','ntt_processed','ntt_complete'))
m.fire('ntt.20')
assert not m.messages and 'ntt_complete' not in m.player.flags
m.advance()
assert m.messages==['ntt.10']
before=(set(m.edges),[(s.x,s.y) for s in stars],list(m.messages))
m.fire('ntt.20')
assert before==(set(m.edges),[(s.x,s.y) for s in stars],list(m.messages))
cleanup_ok(m)
for flag,day in [('ntt_v012_attempted',5),('ntt_pending_verification',5),('',30)]:
    stars,edges,home=galaxy()
    m=Model(stars,edges,home);m.day=day
    m.player.flags.update(('ntt_complete',flag))
    before=(set(m.edges),[(s.x,s.y) for s in stars])
    m.fire('ntt.20')
    assert before==(set(m.edges),[(s.x,s.y) for s in stars])
    assert not m.pending and not m.messages
record('Early v0.1.1 recovery runs once; pending, repeated and day-30-or-later recovery attempts do not run')

validation = '''VALIDATION — 23 October 2026
Starburst Tail Start 0.1.2

These checks passed locally:
''' + ''.join('- '+c+'\n' for c in checks) + '''
The tests parse and execute the shipped scripts in a deliberately limited
Python graph model. The model covers scopes, dynamic relationship flags,
flood-fill selection, layered multi-source BFS tail depth, internal-edge
restoration, delayed verification, failure branches and idempotence.
It is not the Stellaris engine.

Four synthetic 1,000-system layouts cover failure modes in the old tail
filters. These are constructed test cases, not the user's save or actual
Huge galaxy generation. They retain a small attached origin-style pocket,
but cannot establish compatibility with the Mindwardens quest scripts.
The supplied 4.5.2 save was inspected separately. It records 18 systems in
the starting cluster, one external exit, and a radius export of 0.99458.
That evidence corrected the model's 0-100 assumption and exposed the need
to rank by hyperlane depth instead of radial distance.

Additional one-time check, 23 October 2026 (not rerun by this test script):
A conservative replay used the supplied save's 1,000 system coordinates,
hyperlanes, starbase/colony occupancy, auras and fleet presence. All visiting
non-player fleets were excluded, including neutral ones. Recovery selected
a target at depth 44 versus the old exit's depth 18, using the new inner
region definition. A 21-system group retained its internal graph, all six
attached Mindwardens buffer/story systems, ownership, total connectivity
and exactly one external exit in the model. This did not load or modify
the user's save in Stellaris, and does not verify the origin's quest logic.

The placement model uses simple coordinates and does not emulate the game's
collision handling, object ownership bookkeeping, fleet movement, visibility,
psionic aura propagation or scripted origin setup. Scheduled verification
is simulated; the engine's scheduler and event-target persistence are not.

NOT performed: launch in Stellaris, new-game generation in the engine,
save/reload in the engine, multiplayer, achievement verification, or
Mindwardens story playthrough.

API evidence checked against 4.5.1 engine-generated effect/trigger docs.
The submitted save confirms 4.5.2; its installed game files were unavailable.

Use README-FIRST.txt's in-game checks before committing to a campaign.
'''
(PACK/'VALIDATION.txt').write_text(validation)
print(f'\n{len(checks)} check groups passed. No in-game test performed.')

