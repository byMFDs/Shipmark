# Como funciona a comprovação

Um projeto pode conquistar aqui três selos (hallmarks). Cada um é um fato que nós mesmos verificamos, não algo que o autor escreve. Os selos são recalculados toda vez que uma página é exibida, a partir das verificações mais recentes, então um selo que deixou de valer desaparece.

## Repo owner {#authored}

**O que significa:** o repositório do GitHub vinculado ao projeto pertence à conta pessoal do GitHub de quem o publicou. Isso não prova quem escreveu o código.

**Como é verificado:** o autor vincula um repositório público do GitHub e clica em “Verificar repositório”. Consultamos a API pública do GitHub. A marca é conquistada quando o repositório pertence à conta pessoal do GitHub do autor e não é um fork.

Contas e repositórios são comparados pelos ids numéricos do GitHub, não pelos nomes: renomear uma conta ou um repositório não muda nada, e um repositório apagado que alguém recria com o mesmo nome é outro repositório. Só lemos dados públicos: entrar nunca nos dá acesso a repositórios privados.

**O que mais registramos:** quando o repositório foi criado, o primeiro commit dele, quantos commits o autor tem e quando foram o primeiro e o último, e em quantas semanas os commits do autor mudaram código (pelas estatísticas do GitHub; bots não contam). A página do projeto mostra esses fatos em “O que foi verificado”. A marca espera uma breve revisão manual em três casos: o primeiro commit é muito mais antigo que o repositório, o mesmo primeiro commit pertence a um repositório vinculado a outro projeto daqui, ou o GitHub não mostra nenhum commit do autor. As datas dos commits são escritas por quem faz o commit, então descrevem o histórico, mas não o provam.

**Como é verificado de novo:** toda semana buscamos o repositório de novo pelo id.

**Como pode ser perdido:** o repositório é apagado, fica privado ou é transferido para outra conta, ou o autor vincula outro repositório. Um repositório só pode estar vinculado a um projeto.

## Live {#live}

**O que significa:** o autor controla o domínio em que o projeto roda.

**Como é verificado:** o autor adiciona um token que geramos para este projeto e este domínio, de duas maneiras possíveis:

- um registro DNS TXT no domínio, ou
- uma meta tag na página inicial, que precisa carregar publicamente (sem login), responder 200 OK e ter menos de 512 KB.

`www.example.com` e `example.com` contam como o mesmo domínio. Um domínio só pode ser verificado para um projeto por vez. Os tokens são aleatórios e nunca são reutilizados.

**Como é verificado de novo:** uma vez por dia, verificamos de novo todo domínio que não foi confirmado nos últimos 30 dias. O selo só vale enquanto o domínio tiver sido confirmado nos últimos 35 dias.

**Como pode ser perdido:**

- o token sumiu do DNS ou da página inicial: o selo é removido na hora;
- o site ou o DNS não responde: tentamos de novo na próxima execução, mas depois de 35 dias sem confirmação o selo some;
- o autor muda a URL pública para outro domínio.

Toda vez que Live é conquistado ou removido, a mudança fica registrada no nosso registro interno.

O endereço principal de um serviço de hospedagem compartilhado por muitos sites (como `github.io` ou `vercel.app`) não pode ser verificado. O seu próprio endereço nele (`yourname.github.io`) pode.

## Steady {#steady}

**O que significa:** o projeto continua no ar, não só no dia do lançamento.

**Como é verificado:** enquanto um projeto tem Live, acessamos a URL pública dele cerca de a cada 3 horas. Uma verificação tem sucesso quando o site responde com status HTTP abaixo de 400 em até 5 segundos. O selo é conquistado quando, nos últimos 30 dias:

- houve pelo menos 40 verificações, e
- pelo menos 95% delas tiveram sucesso.

A página do projeto mostra a porcentagem de disponibilidade e uma faixa de 30 dias. Os resultados são guardados por 90 dias.

**Como pode ser perdido:** a disponibilidade cai abaixo de 95%, ou o projeto perde Live. Steady sempre exige Live.

Uma verificação também falha quando o site só responde depois de redirecionar para outro domínio: a resposta precisa vir do domínio verificado.

## O que é declarado pelo autor {#self-declared}

Estas partes de um projeto são escritas pelo autor e **não** são verificadas por nós:

- nome, slogan, descrição e capturas de tela;
- tags e data de lançamento;
- “Feito com”, as ferramentas de IA que o autor diz ter usado. Sempre aparece como “declarado pelo autor”.

Os selos dizem só o que dizem. Repo owner trata do repositório, Live do domínio, Steady da disponibilidade. Nenhum deles é uma avaliação do produto.

## O que não podemos verificar {#limits}

O {{ site_name }} verifica fatos que consegue provar: a quem pertence o repositório do GitHub vinculado, quem controla o domínio e se o site responde. Ele não verifica, nem pode verificar, quem escreveu o código. O histórico de commits e as datas são escritos pelo dono do repositório e podem ser alterados. Se você acha que um projeto foi copiado, denuncie.
