# Sobre o {{ site_name }}

O {{ site_name }} é um lugar público onde quem constrói com ferramentas de IA mostra o que realmente lançou. Em vez de afirmações, cada projeto traz selos de comprovação que nós mesmos verificamos.

## O problema {#problem}

Dizer "eu lancei" não custa nada. Uma captura de tela, um post de lançamento ou uma linha no currículo podem descrever qualquer coisa, e de fora ninguém sabe se o produto existe, quem o controla ou se ainda funciona um mês depois.

O GitHub mostra código. O LinkedIn mostra afirmações. O {{ site_name }} tenta mostrar resultados: um projeto, os fatos que conseguimos verificar sobre ele e o que a pessoa fez depois. O principal aqui é o projeto; um perfil é só a coleção de projetos de alguém.

## Como funciona a comprovação {#proof}

Um projeto pode ganhar três selos. Cada um é um fato que o nosso servidor verifica, e cada um desaparece quando o fato deixa de ser verdade.

- **Repo owner.** O projeto vincula um repositório público do GitHub. Perguntamos à API pública do GitHub se ele pertence à conta pessoal do GitHub do autor e não é um fork; em repositórios de organizações e equipes, o autor adiciona em vez disso um arquivo com o token deste projeto. Verificamos de novo toda semana.
- **Domain verified.** O autor prova que controla o domínio do projeto com um token que geramos: um registro TXT no DNS ou uma meta tag na página inicial. Verificamos de novo regularmente, e o selo só vale enquanto o domínio tiver sido confirmado nos últimos 35 dias.
- **Steady.** Quando um projeto tem Domain verified, abrimos o endereço dele mais ou menos a cada 3 horas. Steady exige pelo menos 40 verificações nos últimos 30 dias, e pelo menos 95% delas precisam receber resposta sem erro em até 5 segundos.

As regras completas, incluindo como cada selo pode ser perdido, estão em [Como funciona a comprovação](/how-proof-works/).

## O que não verificamos {#not-verified}

- **Quem escreveu o código.** O {{ site_name }} verifica fatos que consegue provar: a quem pertence o repositório do GitHub vinculado, quem controla o domínio e se o site responde. Ele não verifica, nem pode verificar, quem escreveu o código ou quanto dele foi escrito por uma ferramenta de IA. O histórico de commits e as datas são escritos pelo dono do repositório e podem ser alterados. Se você acha que um projeto foi copiado, denuncie.
- **Se o projeto é bom.** Selos não são avaliações. Um projeto Steady ainda pode ser uma ideia fraca, e um ótimo projeto pode ainda não ter nenhum selo.
- **O que o autor escreve.** Nome, descrição, capturas de tela, tags, data de lançamento e as ferramentas de IA em "Feito com" são informados pelo autor. "Feito com" sempre aparece como declarado pelo autor.

## O que você ganha {#builders}

- Um perfil público que reúne seus projetos. Você entra com o GitHub; pedimos só o seu perfil público e seus endereços de e-mail, nunca acesso aos seus repositórios.
- Uma página para cada projeto com seus selos, capturas de tela, uma faixa de disponibilidade de 30 dias (quando tem Domain verified) e um diário de desenvolvimento: atualizações curtas e notas de lançamento, em ordem.
- Um badge para o README do GitHub ou para o seu site que mostra os selos que o projeto tem agora. O código para colar está na página do projeto.
- Seguir, curtidas, uma página Para você com novos lançamentos e com as pessoas que você segue, e uma página "Descobrir" para encontrar projetos por tag, ferramenta ou selo.
- Controle sobre seus dados: baixe tudo em um arquivo ou exclua sua conta em Configurações. Sem anúncios, sem analytics, sem scripts de rastreamento.

## Quem está por trás {#who}

O {{ site_name }} é construído e mantido por uma pessoa, Danylo Rudenko, desenvolvedor solo. Ele é feito do mesmo jeito que muitos projetos daqui: com ferramentas de IA, principalmente o Claude Code, e uma pessoa decide o que construir e se o resultado está bom.

**TODO (Danylo):** confirme este parágrafo e, se quiser, acrescente uma frase sobre você (onde está, por que começou).

## O que vem depois {#next}

Planejado depois da primeira versão, sem ordem definida:

- uma única página Para você com filtro, em vez de abas separadas;
- avatares e mais formas de personalizar um perfil;
- conquistas;
- verificações melhores de repositórios, por exemplo com forks, e ligar um repositório ao seu domínio;
- o que Domain verified deve significar para projetos que não são sites: ferramentas de linha de comando, bibliotecas, apps móveis.

**TODO (Danylo):** antes de publicar, confira se a lista ainda corresponde aos seus planos.

## Contato {#contact}

Dúvidas, ideias, um bug ou um projeto que não deveria estar aqui: escreva para [{{ contact_email }}](mailto:{{ contact_email }}). Você também pode usar o link "Denunciar" em qualquer projeto ou perfil.

**TODO antes do lançamento:** este endereço vem de `CONTACT_EMAIL` em `config/branding.py` e ainda é provisório.
