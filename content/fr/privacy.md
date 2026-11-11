# Politique de confidentialité

> **Brouillon**, dernière mise à jour le 11 novembre 2026. Ce texte n’a pas encore été relu par un juriste.
>
> Traduction fournie à titre indicatif ; la version anglaise prévaut.

Cette page explique ce que {{ site_name }} conserve à votre sujet, pourquoi, pendant combien de temps, et ce que vous pouvez faire à ce sujet. Elle décrit ce que le site fait réellement.

## Qui est responsable {#controller}

{{ site_name }} est exploité par {{ legal_owner_name }}, qui est responsable de vos données (le « responsable du traitement »).
Questions ou demandes : [{{ contact_email }}](mailto:{{ contact_email }}).

## Ce que nous conservons et pourquoi {#data}

**Lorsque vous vous connectez avec GitHub.** Nous recevons de GitHub l’identifiant de votre compte, votre login, votre nom, votre bio, le lien de votre avatar et les autres champs publics de votre profil GitHub, ainsi que les adresses e-mail de votre compte GitHub. Nous demandons à GitHub uniquement `read:user` et `user:email` : nous n’obtenons jamais d’accès à vos dépôts, privés ou publics, via votre compte. Nous ne conservons pas votre jeton d’accès GitHub après la connexion. Nous avons besoin de ces données pour créer votre compte et vous reconnaître la fois suivante (exécution de notre accord avec vous).

**Votre profil.** Nom d’utilisateur, nom affiché, bio, site web et langue. Le nom et la bio reprennent d’abord vos valeurs GitHub ; vous pouvez les modifier dans les Réglages. Votre nom d’utilisateur, votre nom affiché, votre bio, votre site web, votre login GitHub et le mois de votre inscription sont **publics**.

**Votre adresse e-mail.** Elle est conservée avec votre compte et n’est visible que par notre équipe. Elle n’est jamais affichée sur le site. Le site n’envoie pas d’e-mails ; nous n’utiliserions l’adresse que pour vous contacter au sujet de votre compte ou d’un signalement.

**Vos projets.** Tout ce que vous saisissez : nom, accroche, description, liens, étiquettes, les outils d’IA que vous dites avoir utilisés (affichés comme déclarés par l’auteur), captures d’écran et entrées du journal de développement. Les projets publiés sont publics ; les brouillons ne sont visibles que par vous et notre équipe. Les captures d’écran sont réencodées lors de l’envoi, ce qui supprime les métadonnées cachées comme les informations sur l’appareil photo ou la position GPS.

**Contrôles de preuve.** Pour attribuer des poinçons, nous contrôlons nous-mêmes les faits (notre intérêt légitime à montrer des preuves fiables) :

- *Repo owner :* nous interrogeons l’API publique de GitHub sur le dépôt que vous liez et conservons s’il vous appartient, votre nombre de commits, ainsi que les dates de votre premier et de votre dernier commit. La liste des autres contributeurs fournie par GitHub est lue pendant le contrôle et n’est pas conservée.
- *Live :* nous consultons les enregistrements DNS du domaine de votre projet ou récupérons sa page pour y trouver votre jeton de vérification.
- *Steady :* nous interrogeons l’adresse de votre projet toutes les quelques heures et conservons si elle a répondu et à quelle vitesse. Ces contrôles sont conservés **90 jours**.

Les résultats sont affichés sur la page publique de votre projet.

**Abonnements et mentions J’aime.** Nous conservons les personnes que vous suivez et les projets que vous aimez. Les autres ne voient que les totaux, pas les listes.

**Signalements.** Si vous signalez un projet ou un profil, nous conservons le motif et les détails que vous écrivez. Seule notre équipe voit les signalements. La personne signalée n’est pas informée de qui l’a signalée.

**Acceptation des Conditions.** Nous conservons la version des Conditions que vous avez acceptée et la date.

**Journal d’audit.** Nous tenons un registre interne des changements de poinçons, des actions de modération et des suppressions de comptes, afin de pouvoir vérifier les décisions plus tard. Seule notre équipe peut le consulter.

**Adresses IP et journaux.** L’application ne conserve pas votre adresse IP et ses propres journaux ne la contiennent pas. Pour chaque requête de page, les journaux notent seulement la méthode, l’adresse de la page (sans ce qui suit un `?`), le statut de la réponse, la taille et le temps de traitement, ainsi que les erreurs. Ils ne contiennent aucune information sur votre navigateur. Les adresses de page contiennent des noms d’utilisateur (`/u/<username>/`) : une ligne de journal peut donc montrer quel profil a été ouvert, mais pas par qui.

**Journal des erreurs.** Quand quelque chose échoue, l’application écrit une courte entrée dans un fichier d’erreurs sur notre serveur : l’heure, un numéro de référence aléatoire (celui affiché sur la page d’erreur), la méthode de la requête, l’adresse de la page sans ce qui suit un `?` et avec les noms d’utilisateur remplacés par `[user]`, le statut de la réponse, la partie du code qui a échoué et le message technique, dont sont retirés les adresses e-mail, les adresses IP et tout ce qui ressemble à un mot de passe ou une clé. Les pages introuvables sont écrites dans un fichier séparé, chaque adresse au plus une fois par minute. Ces fichiers ne contiennent jamais votre adresse IP, les informations de votre navigateur, vos cookies, ce que vous saisissez dans les formulaires, votre adresse e-mail ni votre nom d’utilisateur. Chaque fichier est limité à 5 Mo plus 5 copies plus anciennes ; une fois la limite atteinte, la plus ancienne est supprimée.

> **TODO avant le lancement :** le serveur web placé devant l’application tient son propre journal d’accès, qui contient par défaut des adresses IP. Ce qu’il enregistre et combien de temps il le conserve (ainsi que la durée de conservation des journaux de l’application) n’est pas encore décidé. Il faut le compléter, ou désactiver l’enregistrement des IP, avant que cette page ne devienne publique.

**Protection contre les abus.** Pour limiter les abus, nous comptons certaines actions (par exemple les mentions J’aime par heure) dans la base de données du site. Chaque compteur est un nombre lié à votre compte ou à un projet, sans adresse IP, valable 24 heures au plus. Ensuite il n’est plus utilisé, mais la ligne peut rester dans la base jusqu’à son nettoyage.

**Analyse et suivi.** Il n’y en a pas : ni analyse, ni publicité, ni script de suivi. Les polices sont servies depuis notre propre serveur.

**Sauvegardes.** Chaque jour, nous sauvegardons la base de données et les captures d’écran envoyées, et nous conservons chaque sauvegarde 14 jours. Si vous supprimez votre compte, vos données restent dans ces sauvegardes jusqu’au remplacement de la dernière qui les contient, soit 14 jours au plus.

## Combien de temps nous les conservons {#retention}

- Votre compte, profil, projets, abonnements et mentions J’aime : jusqu’à ce que vous les supprimiez, ou que vous supprimiez votre compte.
- Contrôles de disponibilité : 90 jours.
- Sessions de connexion : 2 semaines, ou jusqu’à la déconnexion.
- Signalements que vous avez faits : conservés après traitement. Si vous supprimez votre compte, ils restent sans votre nom.
- Journal d’audit : conservé. Les entrées concernant un compte supprimé ne contiennent ni le nom d’utilisateur ni l’e-mail.
- Compteurs de protection contre les abus : 24 heures au plus.
- Sauvegardes : 14 jours. Un compte supprimé en disparaît dans ce délai de 14 jours.
- Fichiers du journal des erreurs : jusqu’à ce qu’ils soient pleins (5 Mo plus 5 copies de 5 Mo), puis les entrées les plus anciennes sont supprimées.
- Journaux du serveur web et de l’application : **TODO**, pas encore décidé.

## Qui d’autre reçoit des données {#recipients}

- **GitHub, Inc.** Vous vous connectez sur github.com et notre serveur lit votre profil et les données publiques de dépôts depuis l’API de GitHub. La politique de confidentialité propre à GitHub s’applique à votre usage de GitHub.
- **Les serveurs de votre projet.** Pour les contrôles Live et Steady, notre serveur contacte le DNS de votre domaine et l’adresse de votre projet. Ils voient notre serveur, pas vous.
- **Notre hébergeur**, qui exploite pour nous le serveur et la base de données.

Nous ne vendons pas vos données et ne les partageons pas à des fins publicitaires.

## Vos droits {#rights}

- **Consulter et télécharger vos données :** Réglages → « Télécharger mes données » vous donne un fichier JSON avec votre profil, vos informations GitHub, vos projets, votre journal de développement, vos mentions J’aime, vos abonnements et les signalements que vous avez faits.
- **Les corriger :** modifiez votre profil dans les Réglages et vos projets sur leurs pages.
- **Les supprimer :** Réglages → « Supprimer le compte ». Cela supprime aussitôt votre profil et tous vos projets, mentions J’aime et abonnements, et c’est irréversible. Votre nom d’utilisateur redevient libre.
- **Vous opposer ou réclamer :** écrivez à [{{ contact_email }}](mailto:{{ contact_email }}). Si vous vivez dans l’UE, au Royaume-Uni ou en Ukraine, vous pouvez aussi introduire une réclamation auprès de votre autorité de protection des données.

## Cookies {#cookies}

Nous n’utilisons que les cookies nécessaires au fonctionnement du site. Voir la [politique relative aux cookies](/legal/cookies/).

## Modifications {#changes}

Si cette politique change, nous mettons à jour la date en haut. Si le changement est important, nous vous demanderons d’accepter les Conditions mises à jour lors de votre prochaine visite.
