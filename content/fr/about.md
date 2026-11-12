# À propos de {{ site_name }}

{{ site_name }} est un lieu public où les personnes qui construisent avec des outils d'IA montrent ce qu'elles ont réellement lancé. Au lieu d'affirmations, chaque projet porte des poinçons de preuve que nous vérifions nous-mêmes.

## Le problème {#problem}

Dire « je l'ai lancé » ne coûte rien. Une capture d'écran, un post de lancement ou une ligne sur un CV peuvent décrire n'importe quoi, et de l'extérieur personne ne peut savoir si le produit existe, qui le contrôle, ni s'il fonctionne encore un mois plus tard.

GitHub montre du code. LinkedIn montre des affirmations. {{ site_name }} essaie de montrer des résultats : un projet, les faits que nous avons pu vérifier à son sujet, et ce que son auteur a fait ensuite. L'essentiel ici, c'est le projet ; un profil n'est que la collection des projets de quelqu'un.

## Comment fonctionne la preuve {#proof}

Un projet peut obtenir trois poinçons. Chacun est un fait que notre serveur vérifie, et chacun disparaît dès que le fait n'est plus vrai.

- **Repo owner.** Le projet lie un dépôt GitHub public. Nous demandons à l’API publique de GitHub s’il appartient au compte GitHub personnel de l’auteur et n’est pas un fork ; pour les dépôts d’organisations et d’équipes, l’auteur ajoute à la place un fichier contenant le jeton de ce projet. Nous le recontrôlons chaque semaine.
- **Domain verified.** L'auteur prouve qu'il contrôle le domaine du projet avec un jeton que nous générons : un enregistrement TXT dans le DNS ou une balise meta sur la page d'accueil. Nous le revérifions régulièrement, et le poinçon ne tient que tant que le domaine a été confirmé au cours des 35 derniers jours.
- **Steady.** Dès qu'un projet a Domain verified, nous ouvrons son adresse environ toutes les 3 heures. Steady exige au moins 40 vérifications sur les 30 derniers jours, dont au moins 95 % doivent obtenir une réponse sans erreur en moins de 5 secondes.

Les règles complètes, y compris comment chaque poinçon peut être perdu, sont sur [Comment fonctionne la preuve](/how-proof-works/).

## Ce que nous ne vérifions pas {#not-verified}

- **Qui a écrit le code.** {{ site_name }} contrôle les faits qu’il peut prouver : à qui appartient le dépôt GitHub lié, qui contrôle le domaine et si le site répond. Il ne contrôle pas, et ne peut pas contrôler, qui a écrit le code ni quelle part en a écrit un outil d’IA. L’historique des commits et ses dates sont écrits par le propriétaire du dépôt et peuvent être modifiés. Si vous pensez qu’un projet est copié, signalez-le.
- **Si le projet est bon.** Les poinçons ne sont pas des avis. Un projet Steady peut être une idée faible, et un excellent projet peut n'avoir encore aucun poinçon.
- **Ce que l'auteur écrit.** Le nom, la description, les captures, les tags, la date de lancement et les outils d'IA sous « Créé avec » sont indiqués par l'auteur. « Créé avec » est toujours marqué comme déclaré par l'auteur.

## Ce que vous obtenez {#builders}

- Un profil public qui rassemble vos projets. Vous vous connectez avec GitHub ; nous ne demandons que votre profil public et vos adresses e-mail, jamais l'accès à vos dépôts.
- Une page par projet avec ses poinçons, ses captures, une bande de disponibilité sur 30 jours (dès qu'il a Domain verified) et un journal de développement : de courtes mises à jour et des notes de lancement, dans l'ordre.
- Un badge pour votre README GitHub ou votre site, qui affiche les poinçons du projet à l'instant présent. Le code à coller se trouve sur la page du projet.
- Abonnements, j'aime, un fil avec les nouveaux lancements et les personnes que vous suivez, et une page « Explorer » pour trouver des projets par tag, outil ou poinçon.
- La maîtrise de vos données : téléchargez-les toutes dans un fichier ou supprimez votre compte depuis les Réglages. Pas de publicité, pas d'analytique, pas de scripts de pistage.

## Qui est derrière {#who}

{{ site_name }} est construit et géré par une seule personne, Danylo Rudenko, développeur indépendant. Il est fait comme beaucoup de projets ici : avec des outils d'IA, surtout Claude Code, et une personne qui décide de ce qui est construit et vérifie le résultat.

**TODO (Danylo) :** confirme ce paragraphe et, si tu veux, ajoute une phrase sur toi (où tu es, pourquoi tu as commencé).

## La suite {#next}

Prévu après la première version, sans ordre fixe :

- une seule page de fil avec un filtre au lieu d'onglets séparés ;
- des avatars et plus de façons de personnaliser un profil ;
- des succès ;
- de meilleures vérifications des dépôts, par exemple pour les forks, et le lien entre un dépôt et son domaine ;
- ce que Domain verified doit signifier pour les projets qui ne sont pas des sites : outils en ligne de commande, bibliothèques, applications mobiles.

**TODO (Danylo) :** avant publication, vérifie que la liste correspond toujours à tes plans.

## Contact {#contact}

Questions, idées, un bug ou un projet qui ne devrait pas être ici : écrivez à [{{ contact_email }}](mailto:{{ contact_email }}). Vous pouvez aussi utiliser le lien « Signaler » sur n'importe quel projet ou profil.

**TODO avant le lancement :** cette adresse vient de `CONTACT_EMAIL` dans `config/branding.py` et reste provisoire.
