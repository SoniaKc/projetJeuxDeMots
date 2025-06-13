# Consignes d'utilisation

* Commencez par vérifiez que avez bien Python d'insatallé : ouvrez un terminal et tapez 
```bash
python3 --version
``` 
Si la réponse ressemble à "Python 3.12.1", vous avez la bonne version de Python. Sinon, suivez le tutoriel du site officiel : https://www.python.org/downloads/.

* Maintenant que vous avez la bonne version de Python, récupérez le dossier "renduJDM" contenant les documents fournis et placez le où vous le souhaitez dans votre espace de stockage. Les documents sont :
1) un fichier deducAnnoRaff.py
2) un fichier inducAnnoReff.py
3) un fichier synonymeAnnoRaff.py 
4) un fichier transitivitéAnnoRaff.py

* Dans le même répertoire que celui contenant ces 4 fichiers, donc dans "renduJDM", créez un dosser vide et nommez le "cache".

* Ouvrez le dossier "renduJDM" dans votre IDE favori.

Vous êtes à présent libres de modifier et lancer chaque fichier.

# Pour lancer une inférence : 
Sélectionnez le fichier avec l'inférence souhaitée (déduction, induction, synonyme ou transitivité) et tout à la fin du fichier, décommentez la ligne correspondant à l'exemple souhaité. 

Vous pouvez également créer un exemple en respectant la syntaxe et en ajoutant, si elle n'y est pas déjà, la relation voulue dans le dictionnaire "numsRelations" juste au dessus, associée à son numéro dans la base de données JDM.

N'oubliez pas d'enregistrer vos modifications (CTRL+S).

Une fois la ligne décommentée et vos modifications enregistrées, ouvrez un terminal et placez vous dans le dossier où se trouvent les 4 fichiers d'inférence.

Pour lancer un fichier, tapez dans votre terminal :
```bash
python3 [nomDuFichier].py
```

Par exemple, pour lancer deducAnnoRaff.py après vos modifications, tapez : 
```bash
python3 deducAnnoRaff.py
```

### Je vous souhaite de bonnes inférences :)
