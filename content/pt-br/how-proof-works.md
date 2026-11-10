# Como funciona a comprovação

Um projeto pode conquistar aqui três selos (hallmarks). Cada um é um fato que nós mesmos verificamos, não algo que o autor escreve. Os selos são recalculados toda vez que uma página é exibida, a partir das verificações mais recentes, então um selo que deixou de valer desaparece.

## Authored {#authored}

**O que significa:** a pessoa que publicou o projeto escreveu o código, ou uma parte real dele.

**Como é verificado:** o autor vincula um repositório público do GitHub e clica em “Verificar repositório”. Consultamos a API pública do GitHub. O selo é conquistado quando uma destas condições é atendida:

- o repositório pertence à conta pessoal do autor no GitHub e não é um fork, ou
- o GitHub contabiliza pelo menos 10 commits da conta do autor na lista de colaboradores do repositório.

As contas são comparadas pelo id numérico do GitHub, então renomear a conta do GitHub não faz diferença. Lemos apenas dados públicos: entrar na conta nunca nos dá acesso a repositórios privados.

**Como pode ser perdido:** uma verificação posterior encontra o repositório excluído, privado, movido ou que não é mais da conta, ou o autor vincula outro repositório ao projeto. Um repositório só pode estar vinculado a um projeto.

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

## Steady {#steady}

**O que significa:** o projeto continua no ar, não só no dia do lançamento.

**Como é verificado:** enquanto um projeto tem Live, acessamos a URL pública dele cerca de a cada 3 horas. Uma verificação tem sucesso quando o site responde com status HTTP abaixo de 400 em até 5 segundos. O selo é conquistado quando, nos últimos 30 dias:

- houve pelo menos 40 verificações, e
- pelo menos 95% delas tiveram sucesso.

A página do projeto mostra a porcentagem de disponibilidade e uma faixa de 30 dias. Os resultados são guardados por 90 dias.

**Como pode ser perdido:** a disponibilidade cai abaixo de 95%, ou o projeto perde Live. Steady sempre exige Live.

## O que é declarado pelo autor {#self-declared}

Estas partes de um projeto são escritas pelo autor e **não** são verificadas por nós:

- nome, slogan, descrição e capturas de tela;
- tags e data de lançamento;
- “Feito com”, as ferramentas de IA que o autor diz ter usado. Sempre aparece como “declarado pelo autor”.

Os selos dizem só o que dizem. Authored trata do código, Live do domínio, Steady da disponibilidade. Nenhum deles é uma avaliação do produto.
