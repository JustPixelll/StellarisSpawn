"""Execute the actual mod scripts in a small, explicitly limited graph model.
This is NOT Stellaris or an engine compatibility test.
"""
from pathlib import Path
from dataclasses import dataclass, field
import re, math, random, hashlib, json, zipfile, sys

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
    aura: bool=False
    fleets: list=field(default_factory=list)
    planets: list=field(default_factory=list)

@dataclass
class Ctx:
    scope: Obj
    prev: object
    root: Obj

class Model:
    def __init__(self, stars, edges, home, fail=None, nomad=False, origin='origin_default'):
        self.stars=stars
        self.edges={frozenset(e) for e in edges}
        self.player=Obj('player')
        self.player.origin=origin
        self.player.nomad=nomad
        self.home=home
        self.home.owner=self.player
        self.targets={}
        self.messages=[]
        self.fail=fail
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
        if v.startswith('event_target:'): return self.targets.get(v.split(':',1)[1])
        raise ValueError('Unknown ref '+v)

    def flag(self,v,c):
        if '@' in v:
            a,b=v.split('@'); return a+'@'+self.ref(b,c).id
        return v

    def number(self,v,c):
        if v=='trigger:distance_to_core_percent':
            return math.hypot(c.scope.x,c.scope.y)/5
        try: return float(v)
        except ValueError: return c.scope.vars.get(v,0)

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
        if k.startswith('event_target:') or k in ('root','capital_scope','solar_system'):
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
        elif k=='is_same_value': result=c.scope is self.ref(v,c)
        elif k=='has_hyperlane_to': result=frozenset((c.scope,self.ref(v,c))) in self.edges
        elif k=='distance_to_core_percent':
            result=self.compare(math.hypot(c.scope.x,c.scope.y)/5,o,float(v))
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
            elif k.startswith('event_target:') or k in ('root','capital_scope','solar_system'):
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
            elif k in ('set_variable','change_variable'):
                key=get(v,'which'); value=self.number(get(v,'value'),c)
                c.scope.vars[key]=(c.scope.vars.get(key,0)+value) if k=='change_variable' else value
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
            elif k=='country_event': self.messages.append(get(v,'id'))
            elif k in ('log','set_surveyed'): pass
            else: raise ValueError('Unknown effect: '+k)
            i+=1

    def start(self):
        c=Ctx(self.player,None,self.player)
        event=events['ntt.2']
        if self.condition(get(event,'trigger'),c):
            self.run(get(event,'immediate'),c)

def reached(stars,edges,start,blocked=frozenset()):
    seen={start}; todo=[start]
    while todo:
        a=todo.pop()
        for edge in edges:
            if a in edge:
                for b in edge:
                    if b not in seen and b not in blocked: seen.add(b); todo.append(b)
    return seen

def galaxy(seed=0,pocket=0):
    rng=random.Random(seed)
    stars=[Obj('core',40,0)]
    edges=[]
    arms=[]
    for arm in range(6):
        rows=[]
        angle=arm*math.pi/3
        for j in range(1,35):
            row=[]
            for lane in range(3):
                radius=30+13*j
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

checks=[]
def record(label): checks.append(label); print('PASS',label)
def cleanup_ok(m):
    assert not any(any(f.startswith('ntt_') for f in s.flags) for s in m.stars)
    assert not m.player.vars
    assert 'ntt_growing' not in m.player.flags
    assert 'ntt_bad_layout' not in m.player.flags

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

validation = '''VALIDATION — 22 October 2026
Starburst Tail Start 0.1.0

These checks passed locally:
''' + ''.join('- '+c+'\n' for c in checks) + '''
The tests parse and execute the shipped scripts in a deliberately limited
Python graph model. The model covers scopes, dynamic relationship flags,
flood-fill selection, internal-edge restoration, failure branches and
idempotence. It is not the Stellaris engine.

The placement model uses simple coordinates and does not emulate the game's
collision handling, object ownership bookkeeping, fleets, visibility,
psionic aura propagation, scripted origin setup or delayed events.

NOT performed: launch in Stellaris, new-game generation in the engine,
save/reload in the engine, multiplayer, achievement verification, or
Mindwardens story playthrough.

API evidence checked against 4.5.1 engine-generated effect/trigger docs.
4.5.2 is the intended installed version; its game files were not available.

Use README-FIRST.txt's in-game checks before committing to a campaign.
'''
(PACK/'VALIDATION.txt').write_text(validation)
print(f'\n{len(checks)} check groups passed. No in-game test performed.')

