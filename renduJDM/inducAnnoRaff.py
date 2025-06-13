import requests
import json
import math
import re
import os

def getAnnotation(relationID):
    neg = ["improbable","impossible"]
    abstrait = ["hypothétique","métaphore"]
    unPeuNeg = ["non spécifique","peu pertinent","subjectif"]
    pos = ["pertinent","vrai"]
    tresPos = ["constitutif","toujours vrai"]

    urlAnno = f"https://jdm-api.demo.lirmm.fr/v0/relations/from/:r{relationID}"
    repAnno = requests.get(urlAnno)
    dataAnno = repAnno.json()

    # Pas d'annotation, on ignore
    if next(iter(dataAnno)) == "error":
        return 1,None

    listeAnno = []
    for anno in dataAnno["nodes"]:
        if anno["name"] != "Relation:" and anno["name"][:1] != ":r":
            listeAnno.append(anno["name"])

    #print(listeAnno)
    res = 1
    for anno in unPeuNeg:
        if anno in listeAnno:
            res *= 0.5
    for anno in abstrait:        
        if anno in listeAnno:
            res *= 0.5
    for anno in neg:
        if anno in listeAnno:
            res *= 0
    for anno in pos:        
        if anno in listeAnno:
            res *= 1.5
    for anno in tresPos:        
        if anno in listeAnno:
            res *= 1.8

    if "contrastif" in listeAnno:
        return res,-1
    else:
        return res,None



def getRaffinement(noeud1,entite,noeud2):
    urlNomRaf = f"https://jdm-api.demo.lirmm.fr/v0/node_by_id/{entite}"
    dataNomRaf = requests.get(urlNomRaf).json()
    nomEntite = dataNomRaf["name"]

    # Si l'entité est déjà un raffinement, ne pas chercher plus loin
    if ">" in nomEntite:
        return True

    # récupérer tous les raffinements de l'entite
    urlRaf = f"https://jdm-api.demo.lirmm.fr/v0/relations/from/{nomEntite}?types_ids=1"
    filenameRafEntite = re.sub(r'[^\w\-_]', '_', urlRaf)
    dataRaf = ""
    if not os.path.exists(f"cache/{filenameRafEntite}.json"):
        dataRaf = requests.get(urlRaf).json()
        #print("requete 1 faite")
        with open(f'cache/{filenameRafEntite}.json', 'w', encoding='utf-8') as file:
            json.dump(dataRaf, file, indent=4, ensure_ascii=False)
    else:
        with open(f"cache/{filenameRafEntite}.json", "r", encoding="utf-8") as file:
            dataRaf = json.load(file)

    # si l'entité du milieu n'a pas de raffinement, c'est forcement la meme entité partout
    if next(iter(dataRaf)) == "error":
        return True
    
    for node in dataRaf["nodes"]:
        if node["name"] != nomEntite:
            raffinement = node["name"]

            urlN1EFull = f"https://jdm-api.demo.lirmm.fr/v0/relations/from/{noeud1}/to/{raffinement}?wight>0"
            repN1EFull = requests.get(urlN1EFull)
            urlEN2Full = f"https://jdm-api.demo.lirmm.fr/v0/relations/from/{raffinement}/to/{noeud2}?weight>0"
            repEN2Full = requests.get(urlEN2Full)

            dataN1E = repN1EFull.json()
            dataEN2 = repEN2Full.json()

            if next(iter(dataN1E)) != "error" and next(iter(dataEN2)) != "error" and len(dataN1E["relations"]) != 0 and len(dataEN2["relations"]) != 0:
                return True

    return False



def induction(noeud1, noeud2, relationName):
    
    relationNum = numsRelations.get(relationName)

    # récuérer tous les spécifiques de noeud1
    urlGenNoeud1 = f"https://jdm-api.demo.lirmm.fr/v0/relations/from/{noeud1}?types_ids=8&min_weight=1"
    # récupérer tous les noeuds allant vers noeud2 avec la relation relationNum
    urlRToNoeud2 = f"https://jdm-api.demo.lirmm.fr/v0/relations/to/{noeud2}?types_ids={relationNum}&min_weight=1"

    filenameUrl1 = re.sub(r'[^\w\-_]', '_', urlGenNoeud1)
    filenameUrl2 = re.sub(r'[^\w\-_]', '_', urlRToNoeud2)

    dataGenN1 = ""
    dataRN2 = ""
    if not os.path.exists(f"cache/{filenameUrl1}.json"):
        repGenN1 = requests.get(urlGenNoeud1)
        #print("requete 1 faite")
        if repGenN1.status_code == 200:
            dataGenN1 = repGenN1.json()
            with open(f'cache/{filenameUrl1}.json', 'w', encoding='utf-8') as file:
                json.dump(dataGenN1, file, indent=4, ensure_ascii=False)
        else:
            print(f"Erreur {repGenN1.status_code}: Impossible d'accéder au fichier JSON")
    else:
        with open(f"cache/{filenameUrl1}.json", "r", encoding="utf-8") as file:
            dataGenN1 = json.load(file)
        #print("chargement 1 fait")


    if not os.path.exists(f"cache/{filenameUrl2}.json"):
        repRToNoeud2 = requests.get(urlRToNoeud2)
        if repRToNoeud2.status_code == 200:
            dataRN2 = repRToNoeud2.json()
            #print("requete 2 faite")
            with open(f'cache/{filenameUrl2}.json', 'w', encoding='utf-8') as file:
                json.dump(dataRN2, file, indent=4, ensure_ascii=False)
        else:
            print(f"Erreur {repRToNoeud2.status_code}: Impossible d'accéder au fichier JSON")
    else:
        with open(f"cache/{filenameUrl2}.json", "r", encoding="utf-8") as file:
            dataRN2 = json.load(file)
        #print("chargement 2 fait")


    if len(dataGenN1["relations"]) == 0:
        print(f"Non, pas selon JDM || {noeud1} n'a pas de spécifique")
        return 0

    if len(dataRN2["relations"]) == 0:
        print(f"Non, pas selon JDM || il n'y a pas de relation de type {relationNum} vers {noeud2}")
        return 0

    # Enlever les noeuds qui commencent pas "en:" ou qui sont raffinés et les relations liées
    noeudsAnglaisRaf = {node["id"] for node in dataGenN1["nodes"] if node["name"].startswith("en:") or ">" in node["name"]}
    dataGenN1["nodes"] = [node for node in dataGenN1["nodes"] if node["id"] not in noeudsAnglaisRaf]
    dataGenN1["relations"] = [rel for rel in dataGenN1["relations"] if rel["node2"] not in noeudsAnglaisRaf]
  
    maxW = 0
    for relationBrute in dataGenN1["relations"]:
        if relationBrute["w"] > maxW:
            maxW = relationBrute["w"]
    normRelationsGen = dataGenN1["relations"]
    for rel in normRelationsGen:
        rel["w"] = rel["w"]/maxW

    maxW = 0
    for relationBrute in dataRN2["relations"]:
        if relationBrute["w"] > maxW:
            maxW = relationBrute["w"]
    normRelationsR = dataRN2["relations"]
    for rel in normRelationsR:
        rel["w"] = rel["w"]/maxW


    # Récupérer les IDs et les poids des relations des noeuds relatifs aux relations
    entiteGenIDList = {}
    entiteAgentIDList = {}
    # noeud1 - R_hypo - {noeud2}
    for relation in normRelationsGen:
        entiteGenIDList[relation["node2"]] = [relation["w"],relation["id"]]
    # {noeud1} - relationName - noeud2
    for relation in normRelationsR:
        entiteAgentIDList[relation["node1"]] = [relation["w"],relation["id"]]

    # Intersection et moyenne géométrique
    intersectionIDs = {}
    for val in entiteGenIDList.keys():
        if val in entiteAgentIDList.keys():
            # FAIRE UNE UPDATE PAR ANNOTATION avec l'id de la relation
            resAnnoN1Gen,contrasN1Gen = getAnnotation(entiteGenIDList.get(val)[1])
            resAnnoGenN2,contrasGenN2 = getAnnotation(entiteAgentIDList.get(val)[1])
            resAnnoN1Gen = float(resAnnoN1Gen)
            resAnnoGenN2 = float(resAnnoGenN2)

            if contrasN1Gen != None or contrasGenN2 != None:
                # Si Contrastif : FAIRE UNE VERIF DE RAFFINEMENT
                if (getRaffinement(noeud1,val,noeud2)):
                    if contrasN1Gen != None and resAnnoN1Gen > 1:
                        resAnnoN1Gen = 1.8
                    if contrasGenN2 != None and resAnnoGenN2 > 1:
                        resAnnoGenN2 = 1.8
            intersectionIDs[val] = math.sqrt((entiteGenIDList[val][0]*resAnnoN1Gen) * (entiteAgentIDList[val][0]*resAnnoGenN2))
             
    sortedIntersectionIDs = dict(sorted(intersectionIDs.items(), key=lambda item: item[1], reverse=True))


    if not intersectionIDs:
        print(f"Non || Aucune intersection entre les spécifiques de {noeud1} et les noeuds ayant une relation de type {relationName} vers {noeud2}")
        return 0

    # Affichage du résultat
    i=1
    for idNoeud in sortedIntersectionIDs.keys(): 
        for noeud in dataGenN1["nodes"]:
            if noeud["id"] == idNoeud:
                print(f"{i} || oui || {noeud1} -r_hypo-> {noeud["name"]}  >  {noeud["name"]} -{relationName}-> {noeud2} || poids = {intersectionIDs[idNoeud]}")
                i+=1
        if i > 10:
            break

    return 0


    



numsRelations = {"r_isa" : 6 ,
                "r_agent-1" : 24,
                "r_lieu" : 15,
                "r_carac" : 17,
                "r_patient" : 14,
                "r_hypo" : 8,
                "r_holo" : 10}

# Réponse = OUI
induction("couper","pain","r_patient")
#induction("chat","miauler","r_agent-1")

# Réponse = NON
#induction("avocat","pousser","r_agent-1")

#induction("tigre","chasser","r_agent-1")
#induction("pigeon","voler","r_agent-1")
#induction("pigeon","pondre","r_agent-1)
#induction("Airbus A380","attérir","r_agent-1")
#induction("Tour Eiffel","France","r_lieu")
#induction("tigre","dangereux","r_carac")
#induction("serveuse","apporter à boire","r_agent-1")
#induction("couper","poulet","r_patient")

