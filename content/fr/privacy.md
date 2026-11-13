# Politique de confidentialité

> **Brouillon**, dernière mise à jour le 13 novembre 2026. Ce texte n’a pas encore été relu par un juriste.
>
> Traduction fournie à titre indicatif ; la version anglaise prévaut.

Cette page explique ce que {{ site_name }} conserve à votre sujet, pourquoi, pendant combien de temps, et ce que vous pouvez faire à ce sujet. Elle décrit ce que le site fait réellement.

## Qui est responsable {#controller}

{{ site_name }} est exploité par {{ legal_owner_name }}, qui est responsable de vos données (le « responsable du traitement »).
Questions ou demandes : [{{ contact_email }}](mailto:{{ contact_email }}).

## Ce que nous conservons et pourquoi {#data}

**Lorsque vous vous connectez avec GitHub.** Nous recevons de GitHub l’identifiant de votre compte, votre login, votre nom, votre bio, le lien de votre avatar et les autres champs publics de votre profil GitHub, ainsi que les adresses e-mail de votre compte GitHub. Nous demandons à GitHub uniquement `read:user` et `user:email` : nous n’obtenons jamais d’accès à vos dépôts, privés ou publics, via votre compte. Nous ne conservons pas votre jeton d’accès GitHub après la connexion. Nous avons besoin de ces données pour créer votre compte et vous reconnaître la fois suivante (exécution de notre accord avec vous). Votre identifiant GitHub est mis à jour à chaque connexion, pour que votre profil mène toujours à votre compte GitHub actuel.

**Votre profil.** Nom d’utilisateur, nom affiché, phrase d’accroche, « À propos », localisation, un statut (par exemple « Ouvert aux offres »), jusqu’à 10 compétences, jusqu’à 6 liens, jusqu’à 3 projets épinglés et votre langue. Tout sauf le nom d’utilisateur est facultatif. Le nom affiché et « À propos » reprennent d’abord votre nom et votre bio GitHub ; vous pouvez les modifier ou les retirer dans les Réglages. Nous enregistrons aussi l’adresse de votre image GitHub, uniquement pour que « Utiliser mon image GitHub » puisse la copier ; elle n’est jamais affichée. Votre nom d’utilisateur, nom affiché, phrase d’accroche, « À propos », localisation, statut, compétences, liens, projets épinglés, identifiant GitHub et le mois de votre inscription sont **publics**.

**Photo de profil et couverture.** Vous pouvez envoyer une photo et une image de couverture large, ou copier une fois votre image GitHub. Chaque image est réencodée (la photo en 512×512, la couverture en 1500×500), ce qui supprime les métadonnées cachées comme la position GPS, reçoit un nom de fichier aléatoire et est stockée sur notre propre serveur : les pages ne chargent jamais votre photo depuis GitHub. Les deux sont **publiques**. Quand vous en retirez ou remplacez une, ou supprimez votre compte, le fichier est supprimé ; des copies restent dans les sauvegardes jusqu’à 14 jours. Sans photo, vos initiales sont affichées.

**Votre adresse e-mail.** Elle est conservée avec votre compte et n’est visible que par notre équipe. Elle n’est jamais affichée sur le site. Le site ne vous envoie pas d’e-mails (le seul qu’il envoie est un avis à notre équipe au sujet d’un message au support) ; nous n’utiliserions l’adresse que pour vous contacter au sujet de votre compte, d’un signalement ou d’un message au support.

**Vos projets.** Tout ce que vous saisissez : nom, accroche, description, liens, étiquettes, les outils d’IA que vous dites avoir utilisés (affichés comme déclarés par l’auteur), captures d’écran et entrées du journal de développement. Les projets publiés sont publics ; les brouillons ne sont visibles que par vous et notre équipe. Les captures d’écran sont réencodées lors de l’envoi, ce qui supprime les métadonnées cachées comme les informations sur l’appareil photo ou la position GPS.

**Contrôles de preuve.** Pour attribuer des poinçons, nous contrôlons nous-mêmes les faits (notre intérêt légitime à montrer des preuves fiables) :

- *Repo owner :* nous interrogeons l’API publique de GitHub sur le dépôt que vous liez et enregistrons son identifiant, l’identifiant du compte propriétaire, s’il vous appartient, sa date de création et son champ Website, le premier commit de son historique (identifiant et date), votre nombre de commits, les dates de votre premier et de votre dernier commit, le nombre de semaines avec vos commits et l’état d’une vérification manuelle si elle est nécessaire. Nous le recontrôlons chaque semaine. La liste des autres contributeurs est lue pendant le contrôle et n’est pas enregistrée. Si vous utilisez le fichier de vérification pour le dépôt d’une organisation, nous enregistrons aussi s’il a été trouvé.
- *Domain verified :* nous consultons les enregistrements DNS du domaine de votre projet ou récupérons sa page pour y trouver votre jeton de vérification.
- *Steady :* nous interrogeons l’adresse de votre projet toutes les quelques heures et conservons si elle a répondu et à quelle vitesse. Ces contrôles sont conservés **90 jours**.

Les résultats sont affichés sur la page publique de votre projet.

**Abonnements et mentions J’aime.** Nous conservons les personnes que vous suivez et les projets que vous aimez. Les autres ne voient que les totaux, pas les listes.

**Signalements et modération.** Si vous signalez un projet, un profil ou une entrée du journal de développement, nous enregistrons le motif et les détails que vous écrivez. Les signalements sont vus par les modérateurs (personnes ayant le badge de modérateur) et l’équipe. Pour décider, ils voient aussi le contenu signalé et l’historique de la personne signalée sur {{ site_name }} : sa date d’inscription, ses sanctions précédentes, les autres signalements la concernant et ses projets retirés. Les pages de modération n’affichent pas les adresses e-mail. La personne signalée n’apprend jamais qui l’a signalée. Quand les modérateurs agissent, nous enregistrons la décision et son motif : un projet retiré garde son contenu et le motif (seuls vous, les modérateurs et l’équipe le voient), les champs de profil effacés (photo et couverture, phrase d’accroche et « À propos », ou liens) sont supprimés, et les mises en sourdine et bannissements sont enregistrés avec leur motif, leur début et leur fin. Vous voyez le motif dans un avis sur le site, que nous gardons jusqu’à la suppression de votre compte. Les décisions vous concernant et ces avis figurent dans « Télécharger mes données ». Pour contester une décision, écrivez à [{{ contact_email }}](mailto:{{ contact_email }}).

**Communauté.** Quand vous publiez dans la communauté, nous conservons vos fils (rubrique, titre, texte, dates, et si un fil a été modifié, épinglé, verrouillé ou retiré), vos réponses (texte, l’autocollant choisi, le message auquel elles répondent) et les images que vous joignez. Les images sont réencodées comme les captures d’écran : les métadonnées cachées comme la position GPS sont supprimées, les noms de fichiers sont aléatoires, et nous conservons sur notre propre serveur une copie jusqu’à 1600 px et une miniature de 640 px. Les messages, leurs images, leur nombre de votes et votre nom d’utilisateur sont **publics**. Nous conservons aussi vos votes ; personne ne voit qui a voté pour quoi, ni sur le site ni dans l’administration. Quand vous supprimez un message, son texte, son autocollant et ses images sont supprimés immédiatement (le titre d’un fil reste tant que des réponses d’autres personnes s’y trouvent, affiché comme « [supprimé] »). Quand les modérateurs retirent un message, ses images sont supprimées immédiatement et son texte est conservé avec le motif, visible seulement par vous, les modérateurs et l’équipe. Les modérateurs voient les messages signalés avec l’historique de leur auteur, comme pour les autres signalements.

**Notifications de réponses.** Quand quelqu’un répond à votre fil ou à votre réponse, nous conservons une notification pour vous (quelle réponse, quand, et quand vous avez ouvert la liste), ainsi que l’heure de la plus récente non lue, pour que le menu puisse afficher une marque. Vous seul les voyez. Elles sont supprimées après **90 jours**, ou avec votre compte. Nous ne les envoyons jamais par e-mail.

**Contournement d’un bannissement.** Quand un compte est banni, nous conservons une empreinte à sens unique, salée, de son identifiant GitHub (jamais l’identifiant lui-même), avec le motif et la date de fin. Elle sert uniquement à reconnaître le même compte GitHub s’il se réinscrit pendant le bannissement. Elle est supprimée quand le bannissement prend fin ou est levé, y compris si le compte banni a été supprimé entre-temps.

**Acceptation des Conditions.** Nous conservons la version des Conditions que vous avez acceptée et la date.

**Journal d’audit.** Nous tenons un registre interne des changements de poinçons, des actions de modération et des suppressions de comptes, afin de pouvoir vérifier les décisions plus tard. Seule notre équipe peut le consulter.

**Adresses IP et journaux.** L’application ne conserve pas votre adresse IP et ses propres journaux ne la contiennent pas. Pour chaque requête de page, les journaux notent seulement la méthode, l’adresse de la page (sans ce qui suit un `?`), le statut de la réponse, la taille et le temps de traitement, ainsi que les erreurs. Ils ne contiennent aucune information sur votre navigateur. Les adresses de page contiennent des noms d’utilisateur (`/u/<username>/`) : une ligne de journal peut donc montrer quel profil a été ouvert, mais pas par qui.

**Journal des erreurs.** Quand quelque chose échoue, l’application écrit une courte entrée dans un fichier d’erreurs sur notre serveur : l’heure, un numéro de référence aléatoire (celui affiché sur la page d’erreur), la méthode de la requête, l’adresse de la page sans ce qui suit un `?` et avec les noms d’utilisateur remplacés par `[user]`, le statut de la réponse, la partie du code qui a échoué et le message technique, dont sont retirés les adresses e-mail, les adresses IP et tout ce qui ressemble à un mot de passe ou une clé. Les pages introuvables sont écrites dans un fichier séparé, chaque adresse au plus une fois par minute. Ces fichiers ne contiennent jamais votre adresse IP, les informations de votre navigateur, vos cookies, ce que vous saisissez dans les formulaires, votre adresse e-mail ni votre nom d’utilisateur. Chaque fichier est limité à 5 Mo plus 5 copies plus anciennes ; une fois la limite atteinte, la plus ancienne est supprimée.

> **TODO avant le lancement :** le serveur web placé devant l’application tient son propre journal d’accès, qui contient par défaut des adresses IP. Ce qu’il enregistre et combien de temps il le conserve (ainsi que la durée de conservation des journaux de l’application) n’est pas encore décidé. Il faut le compléter, ou désactiver l’enregistrement des IP, avant que cette page ne devienne publique.

**Protection contre les abus.** Pour limiter les abus, nous comptons certaines actions (par exemple les mentions J’aime par heure) dans la base de données du site. Chaque compteur est un nombre lié à votre compte ou à un projet, sans adresse IP, valable 24 heures au plus. Ensuite il n’est plus utilisé, mais la ligne peut rester dans la base jusqu’à son nettoyage.

**Analyse et suivi.** Il n’y en a pas : ni analyse, ni publicité, ni script de suivi. Les polices sont servies depuis notre propre serveur.

**Sauvegardes.** Chaque jour, nous sauvegardons la base de données et les images envoyées (captures, photos de profil et couvertures) et gardons chaque sauvegarde 14 jours. Si vous supprimez votre compte, vos données restent dans ces sauvegardes jusqu’au remplacement de la dernière qui les contient, soit au plus 14 jours.

## Messages au support {#support}

Quand vous nous écrivez via le [formulaire de support](/support/), nous conservons le sujet, l’objet, votre message, l’adresse e-mail indiquée (ou celle de votre compte), le compte avec lequel vous étiez connecté, le numéro de référence d’une page d’erreur si vous en venez, et jusqu’à 3 pièces jointes. Les images sont réencodées comme les autres (les métadonnées cachées comme la position GPS sont supprimées) ; les fichiers texte sont conservés en texte. Les pièces jointes sont stockées dans un dossier privé de notre serveur sans adresse publique : seule l’équipe ayant accès à la boîte du support peut les télécharger. Nous utilisons votre adresse e-mail uniquement pour vous répondre.

Nous ne conservons ni votre adresse IP ni les informations de votre navigateur avec le message. Pour arrêter le spam, une empreinte salée à sens unique de votre adresse IP est gardée dans le cache du serveur 24 heures au plus, jamais dans la base de données ni dans les journaux.

Quand un message arrive, notre serveur envoie à la boîte de l’équipe un court avis en texte brut avec votre message et votre adresse e-mail, via notre fournisseur de messagerie (voir « Qui d’autre reçoit des données »). L’équipe peut ajouter des notes internes et indiquer un statut (nouveau, lu, répondu, clos). Nous lisons chaque message mais ne pouvons pas promettre de répondre à tous. Les messages clos sont supprimés 12 mois après leur envoi ; les autres restent jusqu’à leur clôture. « Télécharger mes données » contient les messages envoyés en étant connecté, et la suppression de votre compte les supprime, ainsi que ceux envoyés sans connexion depuis l’adresse e-mail de votre compte.

## Combien de temps nous les conservons {#retention}

- Votre compte, profil, projets, abonnements et mentions J’aime : jusqu’à ce que vous les supprimiez, ou que vous supprimiez votre compte.
- Messages au support et pièces jointes : clos, 12 mois après l’envoi ; les autres, jusqu’à leur clôture ; avec votre compte.
- Fils, réponses et images de la communauté : jusqu’à ce que vous les supprimiez ou supprimiez votre compte (ce qui reste est décrit plus haut, dans « Communauté »). Votes : jusqu’à ce que vous les retiriez ou supprimiez votre compte.
- Notifications de réponses : 90 jours.
- Photo de profil et couverture : jusqu’à ce que vous les retiriez ou remplaciez, ou supprimiez votre compte.
- Contrôles de disponibilité : 90 jours.
- Décisions de modération vous concernant (mises en sourdine, bannissements, projets retirés) et avis : tant que votre compte existe ; ils sont supprimés avec lui. Les signalements à votre sujet restent sans lien avec votre compte, avec seulement le nom affiché à l’époque.
- Empreinte de l’identifiant GitHub d’un compte banni : seulement jusqu’à la fin ou la levée du bannissement.
- Sessions de connexion : 2 semaines, ou jusqu’à la déconnexion.
- Signalements que vous avez faits : conservés après traitement. Si vous supprimez votre compte, ils restent sans votre nom.
- Journal d’audit : conservé. Les entrées concernant un compte supprimé ne contiennent ni le nom d’utilisateur ni l’e-mail.
- Compteurs de protection contre les abus : 24 heures au plus.
- Sauvegardes : 14 jours. Un compte supprimé en disparaît dans ce délai de 14 jours.
- Fichiers du journal des erreurs : jusqu’à ce qu’ils soient pleins (5 Mo plus 5 copies de 5 Mo), puis les entrées les plus anciennes sont supprimées.
- Journaux du serveur web et de l’application : **TODO**, pas encore décidé.

## Qui d’autre reçoit des données {#recipients}

- **GitHub, Inc.** Vous vous connectez sur github.com et notre serveur lit votre profil et les données publiques de dépôts depuis l’API de GitHub. La politique de confidentialité propre à GitHub s’applique à votre usage de GitHub.
- **Notre fournisseur de messagerie** (par exemple Google, si la boîte de l’équipe est un compte Gmail) achemine vers la boîte de l’équipe l’avis de chaque message au support, avec son texte et votre adresse e-mail.
- **Les serveurs de votre projet.** Pour les contrôles Domain verified et Steady, notre serveur contacte le DNS de votre domaine et l’adresse de votre projet. Ils voient notre serveur, pas vous.
- **Notre hébergeur**, qui exploite pour nous le serveur et la base de données.

Nous ne vendons pas vos données et ne les partageons pas à des fins publicitaires.

## Vos droits {#rights}

- **Consulter et télécharger vos données :** Réglages → « Télécharger mes données » vous donne un fichier JSON avec votre profil (avec vos liens, compétences, projets épinglés et les adresses de votre photo et de votre couverture), vos informations GitHub, vos projets, votre journal de développement, vos mentions J’aime, vos abonnements, les signalements que vous avez faits, ainsi que les décisions de modération et avis vous concernant.
- **Les corriger :** modifiez votre profil dans les Réglages et vos projets sur leurs pages.
- **Les supprimer :** Réglages → « Supprimer le compte ». Cela supprime aussitôt votre profil, votre photo et votre couverture et tous vos projets, mentions J’aime et abonnements, et c’est irréversible. Votre nom d’utilisateur redevient libre.
- **Communauté :** « Télécharger mes données » contient aussi vos fils, vos réponses, les adresses de vos images, vos votes et vos notifications de réponses. Supprimer votre compte supprime vos images de la communauté, vos votes, vos notifications et vos fils sans réponse d’autres personnes ; vos autres messages restent, sans votre nom, votre photo ni votre lien. Les images de la communauté sont dans les sauvegardes quotidiennes, comme les autres fichiers envoyés (14 jours).
- **Vous opposer ou réclamer :** écrivez à [{{ contact_email }}](mailto:{{ contact_email }}). Si vous vivez dans l’UE, au Royaume-Uni ou en Ukraine, vous pouvez aussi introduire une réclamation auprès de votre autorité de protection des données.

## Cookies {#cookies}

Nous n’utilisons que les cookies nécessaires au fonctionnement du site. Voir la [politique relative aux cookies](/legal/cookies/).

## Modifications {#changes}

Si cette politique change, nous mettons à jour la date en haut. Si le changement est important, nous vous demanderons d’accepter les Conditions mises à jour lors de votre prochaine visite.
