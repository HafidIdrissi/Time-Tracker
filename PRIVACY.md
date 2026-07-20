# Politique de confidentialité — Local Time Tracker

Dernière mise à jour : 20 juillet 2026

## Résumé

Local Time Tracker est conçu pour fonctionner entièrement sur l’ordinateur de
l’utilisateur. Il ne nécessite aucun compte et n’envoie aucune donnée vers un
serveur, le développeur ou un service d’analyse.

## Données enregistrées

Lorsque le suivi est actif, l’application enregistre :

- le nom du processus de l’application au premier plan ;
- le titre de la fenêtre ou de l’onglet actif ;
- les heures de début et de fin de chaque période ;
- la durée de chaque période ;
- l’état actif ou inactif déterminé à partir des entrées clavier et souris.

Les titres de fenêtres peuvent contenir des informations sensibles, par exemple
des noms de documents, des recherches, des sujets de messages ou des noms de
projets.

## Finalité

Ces informations sont utilisées uniquement pour afficher le tableau de bord,
calculer les statistiques d’utilisation et générer les rapports demandés par
l’utilisateur.

## Stockage

Les données sont conservées dans une base SQLite locale. Pour une installation
Windows standard, elles se trouvent dans :

```text
%LOCALAPPDATA%\LocalTimeTracker\data\activity.db
```

Les rapports HTML générés sont stockés dans le même dossier local, sous
`reports/`.

## Transmission et services tiers

L’application :

- ne transmet pas l’historique d’activité ;
- n’utilise aucun outil de télémétrie ou de publicité ;
- n’intègre aucun traceur ;
- ne vend ni ne partage de données ;
- ne nécessite aucune connexion Internet pour fonctionner.

GitHub ou une plateforme de téléchargement peut enregistrer ses propres données
techniques lorsqu’un utilisateur visite une page ou télécharge l’installateur.
Ces traitements relèvent de la politique de la plateforme concernée et non de
l’application locale.

## Contrôle et suppression

L’utilisateur peut effacer l’historique depuis le bouton **Réinitialiser** de
l’application. La désinstallation officielle supprime également les données
locales créées par l’application.

## Sécurité

Les données ne sont pas chiffrées par l’application. Elles bénéficient des
protections du compte Windows et du disque de l’utilisateur. Toute personne
ayant accès au compte ou au fichier SQLite peut potentiellement les consulter.

## Modifications

Cette politique peut être mise à jour lors d’un changement de fonctionnalité.
La date placée en haut du document indique la dernière révision.

## Contact

Développeur : Hafid Idrissi  
Support public : https://github.com/HafidIdrissi/Time-Tracker/issues

Une adresse e-mail publique et, lorsque la plateforme de distribution l’exige,
une adresse postale professionnelle doivent être ajoutées avant publication sur
un catalogue tiers.
