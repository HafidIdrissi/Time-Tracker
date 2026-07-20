# Signature des versions Windows

La version locale peut être construite sans certificat, mais une distribution
publique professionnelle doit utiliser une signature Authenticode délivrée par
une autorité reconnue par Windows.

## Pourquoi signer

La signature permet à Windows et aux plateformes de téléchargement de vérifier :

- l’identité de l’éditeur ;
- que le fichier n’a pas été modifié après sa publication ;
- que les versions successives proviennent du même éditeur.

Un certificat auto-signé est utile pour des tests internes, mais il n’est pas
considéré comme fiable sur les ordinateurs des utilisateurs et ne convient pas à
une publication Softonic.

## Options possibles

### Projet open source

Vérifier l’éligibilité à SignPath Foundation, qui propose une signature gratuite
à certains projets open source : https://signpath.org/activities/foundation/

### Distribution directe

Utiliser un certificat OV provenant d’une autorité reconnue ou un service de
signature pris en charge par Microsoft. Le certificat implique une vérification
d’identité et peut être payant.

### Microsoft Store

Une publication MSIX via le Microsoft Store est signée par Microsoft après
validation. Ce chemin demande un packaging MSIX distinct de l’installateur Inno
Setup actuel.

## Signature locale avec SignTool

Après obtention d’un certificat installé dans le magasin Windows, localiser
`signtool.exe` dans le Windows SDK puis définir :

```powershell
$env:TIME_TRACKER_SIGNTOOL = "C:\Program Files (x86)\Windows Kits\10\bin\VERSION\x64\signtool.exe"
$env:TIME_TRACKER_CERT_SHA1 = "EMPREINTE_SHA1_DU_CERTIFICAT"
.\build_release.ps1
```

Le script signe alors :

1. `dist\LocalTimeTracker\LocalTimeTracker.exe` avant son intégration ;
2. `release\LocalTimeTracker-Setup-1.0.0-x64.exe` après sa création ;
3. recalcule le SHA-256 sur le fichier signé final.

Les variables et certificats de signature ne doivent jamais être ajoutés au
dépôt Git.
