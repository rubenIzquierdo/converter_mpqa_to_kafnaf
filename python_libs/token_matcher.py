#!/usr/bin/env python


#####
# 4-Mar-2013 : modified order of rules to check first if there is a merge and then if it is an extra token
#  becuase of this case, where can be both:  [ .. . ]  [ . . . ]       
  
  
def add_match(d,id_new,id_ref):
  if id_new in d:
    d[id_new].append(id_ref)
  else:
    d[id_new]=[id_ref]
    
    
def token_matcher(l_ref,l_new,super_d):
  #print l_ref
  #print l_new
  if len(l_new)==0:
    return
  else:
    #print 'l_REF',l_ref
    token_ref, id_ref = l_ref[0]
    token_new, id_new = l_new[0]
    if token_ref == token_new:
      #print 'Matching ',l_ref[0],l_new[0]
      #print 'A',l_ref[0],l_new[0]      
      add_match(super_d,id_new,id_ref)
      token_matcher(l_ref[1:],l_new[1:],super_d)
    else:
      if token_ref.startswith(token_new)  : ##There was an split
        #print 'D'
        aux = (token_ref[len(token_new):],id_ref)
        l_ref[0]=aux
        
        add_match(super_d,id_new,id_ref)
        token_matcher(l_ref,l_new[1:],super_d)
      
      elif token_new.startswith(token_ref)  : ##There was a merge
        #print 'E'
        aux = (token_new[len(token_ref):],id_new)
        l_new[0]=aux
        add_match(super_d,id_new,id_ref)
        token_matcher(l_ref[1:],l_new,super_d)


      elif len(l_new)>1 and l_new[1][0]==token_ref: ## There is an extra token in l_new
        #print 'B',l_new[1][0],token_ref
        token_matcher(l_ref[0:],l_new[1:],super_d)
      
        
      elif len(l_ref)>1 and l_ref[1][0] == token_new: ## There is an extra token in l_ref
        #print 'C',l_ref[1:],l_new[0:]
        token_matcher(l_ref[1:],l_new[0:],super_d)
        
      
      else: ## Imposible matching
        #print 'F'
        #print 'Impossible match of ',l_new[0],l_ref[0]
        token_matcher(l_ref[1:],l_new[1:],super_d)


if __name__ == '__main__':
  l1 = []
  s1 = 'Beatrix Wilhelmina Armgard van Oranje -Nassau (Baarn , 31 januari 1938 ) is sinds 30 april 1980 koningin van het Koninkrijk der Nederlanden'
  
  s1 = 'Th is is a very simple example'
  for n,t in enumerate(s1.split(' ')):
    l1.append((t,'id'+str(n)))

  l2 = []
  #s2 = 'Beatrix Wilhelmina Armgard van Oranje -Nassau ( Baarn , 31 januari 1938 ) is sinds 30 april 1980 koningin van het Koninkrijk der Nederlanden'
  s2 = 'This is a very sim ple example'
  for n,t in enumerate(s2.split(' ')):
    l2.append((t,'id'+str(n))) 

  super_d = {}
  token_matcher(l1,l2,super_d)
  print l1
  print l2
  print super_d