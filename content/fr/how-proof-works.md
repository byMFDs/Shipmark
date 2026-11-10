# Comment fonctionne la preuve

Un projet peut obtenir ici trois poinçons (hallmarks). Chacun est un fait que nous contrôlons nous-mêmes, pas quelque chose que l’auteur saisit. Les poinçons sont recalculés à chaque affichage d’une page, à partir des derniers contrôles : un poinçon qui n’est plus justifié disparaît.

## Authored {#authored}

**Ce que cela signifie :** la personne qui a publié le projet a écrit le code, ou une part réelle de celui-ci.

**Comment c’est contrôlé :** l’auteur lie un dépôt GitHub public et clique sur « Contrôler le dépôt ». Nous interrogeons l’API publique de GitHub. Le poinçon est obtenu lorsque l’une de ces conditions est remplie :

- le dépôt appartient au compte GitHub personnel de l’auteur et n’est pas un fork, ou
- GitHub compte au moins 10 commits du compte de l’auteur dans la liste des contributeurs du dépôt.

Les comptes sont comparés par l’identifiant numérique GitHub, donc renommer un compte GitHub n’a aucune incidence. Nous ne lisons que des données publiques : la connexion ne nous donne jamais accès aux dépôts privés.

**Comment il peut être perdu :** un contrôle ultérieur constate que le dépôt est supprimé, privé, déplacé ou n’est plus l’œuvre du compte, ou l’auteur lie un autre dépôt au projet. Un dépôt ne peut être lié qu’à un seul projet.

## Live {#live}

**Ce que cela signifie :** l’auteur contrôle le domaine sur lequel le projet fonctionne.

**Comment c’est contrôlé :** l’auteur ajoute un jeton que nous générons pour ce projet et ce domaine, de l’une des deux façons suivantes :

- un enregistrement DNS TXT sur le domaine, ou
- une balise meta sur la page d’accueil, qui doit se charger publiquement (sans connexion), répondre 200 OK et peser moins de 512 Ko.

`www.example.com` et `example.com` comptent comme le même domaine. Un domaine ne peut être vérifié que pour un seul projet à la fois. Les jetons sont aléatoires et jamais réutilisés.

**Comment il est recontrôlé :** une fois par jour, nous recontrôlons chaque domaine qui n’a pas été confirmé au cours des 30 derniers jours. Le poinçon n’est valable que si le domaine a été confirmé au cours des 35 derniers jours.

**Comment il peut être perdu :**

- le jeton a disparu du DNS ou de la page d’accueil : le poinçon est retiré immédiatement ;
- le site ou le DNS ne répond pas : nous réessayons au passage suivant, mais après 35 jours sans confirmation, le poinçon disparaît ;
- l’auteur change l’URL publique pour un autre domaine.

Chaque fois que Live est obtenu ou retiré, le changement est consigné dans notre journal interne.

## Steady {#steady}

**Ce que cela signifie :** le projet reste en ligne, pas seulement le jour du lancement.

**Comment c’est contrôlé :** tant qu’un projet a Live, nous interrogeons son URL publique environ toutes les 3 heures. Un contrôle réussit lorsque le site répond avec un statut HTTP inférieur à 400 en moins de 5 secondes. Le poinçon est obtenu lorsque, sur les 30 derniers jours :

- il y a eu au moins 40 contrôles, et
- au moins 95 % ont réussi.

La page du projet affiche le pourcentage de disponibilité et une bande de 30 jours. Les résultats sont conservés 90 jours.

**Comment il peut être perdu :** la disponibilité tombe sous 95 %, ou le projet perd Live. Steady exige toujours Live.

## Ce qui est déclaré par l’auteur {#self-declared}

Ces éléments d’un projet sont rédigés par l’auteur et ne sont **pas** contrôlés par nous :

- nom, accroche, description et captures d’écran ;
- étiquettes et date de lancement ;
- « Créé avec », les outils d’IA que l’auteur dit avoir utilisés. C’est toujours indiqué comme « déclaré par l’auteur ».

Les poinçons disent seulement ce qu’ils disent. Authored concerne le code, Live le domaine, Steady la disponibilité. Aucun n’est une évaluation du produit.
