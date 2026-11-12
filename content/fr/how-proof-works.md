# Comment fonctionne la preuve

Un projet peut obtenir ici trois poinçons (hallmarks). Chacun est un fait que nous contrôlons nous-mêmes, pas quelque chose que l’auteur saisit. Les poinçons sont recalculés à chaque affichage d’une page, à partir des derniers contrôles : un poinçon qui n’est plus justifié disparaît.

## Repo owner {#authored}

**Ce que cela signifie :** le dépôt GitHub lié au projet appartient au compte GitHub personnel de la personne qui l’a publié ou (pour les dépôts d’organisations et d’équipes) contient le fichier de vérification de ce projet, ce qui exige un accès en écriture. Cela ne prouve pas qui a écrit le code.

**Comment c’est contrôlé :** l’auteur lie un dépôt GitHub public et clique sur « Contrôler le dépôt ». Nous interrogeons l’API publique de GitHub. La marque est obtenue quand le dépôt appartient au compte GitHub personnel de l’auteur et n’est pas un fork.

**Dépôts d’organisations et d’équipes :** la page de modification donne à chaque projet son propre jeton aléatoire. Ajoutez à la racine de la branche par défaut un fichier nommé `.shipmark-verify` qui contient uniquement ce jeton, puis contrôlez à nouveau. Seules les personnes qui peuvent pousser dans le dépôt peuvent l’ajouter : il prouve un accès en écriture, pas qui a écrit le code. Les forks ne comptent jamais, quelle que soit la voie. Le fichier est recontrôlé chaque semaine ; s’il a disparu, la marque est retirée.

Les comptes et les dépôts sont comparés par les identifiants numériques de GitHub, pas par leur nom : renommer un compte ou un dépôt ne change rien, et un dépôt supprimé que quelqu’un recrée sous le même nom est un autre dépôt. Nous ne lisons que des données publiques : la connexion ne nous donne jamais accès aux dépôts privés.

**Ce que nous enregistrons aussi :** la date de création du dépôt, son premier commit, le nombre de commits de l’auteur et les dates du premier et du dernier, et le nombre de semaines où ses commits ont modifié du code (d’après les statistiques de GitHub ; les bots ne comptent pas). La page du projet présente ces faits sous « Ce qui a été contrôlé ». La marque attend une courte vérification manuelle dans trois cas : le premier commit est bien plus ancien que le dépôt, le même premier commit appartient au dépôt d’un autre projet ici, ou GitHub n’affiche aucun commit de l’auteur. Les dates des commits sont écrites par la personne qui fait le commit : elles décrivent l’historique, elles ne le prouvent pas.

**Comment c’est recontrôlé :** chaque semaine, nous retrouvons le dépôt par son identifiant.

**Comment il peut être perdu :** le dépôt est supprimé, rendu privé ou transféré à un autre compte, ou l’auteur lie un autre dépôt. Un dépôt ne peut être lié qu’à un seul projet.

## Domain verified {#live}

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

Chaque fois que Domain verified est obtenu ou retiré, le changement est consigné dans notre journal interne.

L’adresse principale d’un hébergeur partagé par de nombreux sites (comme `github.io` ou `vercel.app`) ne peut pas être vérifiée. Votre propre adresse chez lui (`yourname.github.io`) le peut.

## Steady {#steady}

**Ce que cela signifie :** le projet reste en ligne, pas seulement le jour du lancement.

**Comment c’est contrôlé :** tant qu’un projet a Domain verified, nous interrogeons son URL publique environ toutes les 3 heures. Un contrôle réussit lorsque le site répond avec un statut HTTP inférieur à 400 en moins de 5 secondes. Le poinçon est obtenu lorsque, sur les 30 derniers jours :

- il y a eu au moins 40 contrôles, et
- au moins 95 % ont réussi.

La page du projet affiche le pourcentage de disponibilité et une bande de 30 jours. Les résultats sont conservés 90 jours.

**Comment il peut être perdu :** la disponibilité tombe sous 95 %, ou le projet perd Domain verified. Steady exige toujours Domain verified.

Un contrôle échoue aussi quand le site ne répond qu’après une redirection vers un autre domaine : la réponse doit venir du domaine vérifié.

## Ce qui est déclaré par l’auteur {#self-declared}

Ces éléments d’un projet sont rédigés par l’auteur et ne sont **pas** contrôlés par nous :

- nom, accroche, description et captures d’écran ;
- étiquettes et date de lancement ;
- « Créé avec », les outils d’IA que l’auteur dit avoir utilisés. C’est toujours indiqué comme « déclaré par l’auteur ».

Les poinçons disent seulement ce qu’ils disent. Repo owner concerne le dépôt, Domain verified le domaine, Steady la disponibilité. Aucun n’est une évaluation du produit.

## Ce que nous ne pouvons pas contrôler {#limits}

{{ site_name }} contrôle les faits qu’il peut prouver : à qui appartient le dépôt GitHub lié, qui contrôle le domaine et si le site répond. Il ne contrôle pas, et ne peut pas contrôler, qui a écrit le code. L’historique des commits et ses dates sont écrits par le propriétaire du dépôt et peuvent être modifiés. Si vous pensez qu’un projet est copié, signalez-le.
