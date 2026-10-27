"""Small, versioned JSON schemas; semantic and cross-reference checks are separate."""
from jsonschema import Draft202012Validator

TEXT={'type':'string'}
EVIDENCE={'type':'object','required':['path','line'],'properties':{'path':TEXT,'line':{'type':'integer','minimum':1}}}
BLOCK={'type':'object','required':['kind'],'properties':{'kind':{'enum':['paragraph','heading','table','image','code']},'value':{},'path':TEXT,'alt':TEXT,'level':{'type':'integer','minimum':1,'maximum':6}},'allOf':[
    {'if':{'properties':{'kind':{'const':'table'}}},'then':{'required':['value'],'properties':{'value':{'type':'array','minItems':1,'items':{'type':'array'}}}}},
    {'if':{'properties':{'kind':{'enum':['paragraph','heading','code']}}},'then':{'required':['value'],'properties':{'value':TEXT}}},
    {'if':{'properties':{'kind':{'const':'image'}}},'then':{'required':['path']}}]}
DOC={'type':'object','required':['title','sections'],'properties':{'title':TEXT,'sections':{'type':'array','minItems':1,'items':{
    'type':'object','required':['title','blocks'],'properties':{'title':TEXT,'blocks':{'type':'array','items':BLOCK}}}}}}
SCHEMAS={
 'skeleton':{'type':'object','required':['id','name','kind','path','dependencies','ready_for_detail'],
    'properties':{'id':{'type':'string','pattern':'^[A-Za-z0-9_-]+$'},'name':TEXT,'kind':{'enum':['screen','common']},
                  'path':TEXT,'dependencies':{'type':'array','items':TEXT,'uniqueItems':True},'ready_for_detail':{'type':'boolean'}}},
 'feature':{'type':'object','required':['schema','id','name','kind','dependencies','items','events','data_relations','scenarios'],
    'properties':{'schema':{'const':'contextbase.feature.v1'},'id':TEXT,'name':TEXT,'dependencies':{'type':'object','additionalProperties':{'type':'string','pattern':'^[a-f0-9]{64}$'}},
      'items':{'type':'array','items':{'type':'object','required':['id','name','io','type','required'],'properties':{'id':TEXT,'io':{'enum':['I','O','I／O','‐']}}}},
      'events':{'type':'array','items':{'type':'object','required':['id','name','trigger'],'properties':{'id':TEXT,'name':TEXT}}},
      'data_relations':{'type':'array','items':{'type':'object','required':['kind','store','operation']}},'scenarios':{'type':'array'}}},
 'resolved':{'type':'object','required':['schema','project','foundation_generation','source_snapshot','documents','assets'],
   'properties':{'schema':{'const':'contextbase.resolved.v1'},'foundation_generation':TEXT,'source_snapshot':TEXT,
      'documents':{'type':'array','minItems':1,'items':{'type':'object','required':['path','model'],'properties':{'path':TEXT,'model':DOC}}},
      'assets':{'type':'array','items':{'type':'object','required':['source','destination','sha256'],'properties':{'sha256':{'type':'string','pattern':'^[a-f0-9]{64}$'}}}}}}
}
for value in SCHEMAS.values():value['$schema']='https://json-schema.org/draft/2020-12/schema'


def validate(name,value):
    validator=Draft202012Validator(SCHEMAS[name])
    errors=sorted(validator.iter_errors(value),key=lambda e:str(list(e.path)))
    if errors:
        raise ValueError(name+' schema: '+'; '.join(str(list(e.path))+': '+e.message for e in errors[:5]))
