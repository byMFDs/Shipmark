# Política de privacidade

> **Rascunho**, última atualização em 11 de novembro de 2026. Este texto ainda não foi revisado por um advogado.
>
> Tradução por conveniência; a versão em inglês prevalece.

Esta página explica o que o {{ site_name }} guarda sobre você, por quê, por quanto tempo e o que você pode fazer a respeito. Ela descreve o que o site realmente faz.

## Quem é o responsável {#controller}

O {{ site_name }} é mantido por {{ legal_owner_name }}, que é responsável pelos seus dados (o “controlador”).
Dúvidas ou solicitações: [{{ contact_email }}](mailto:{{ contact_email }}).

## O que guardamos e por quê {#data}

**Quando você entra com o GitHub.** Recebemos do GitHub o id da sua conta, seu login, nome, bio, o link do seu avatar e os demais campos públicos do seu perfil do GitHub, além dos endereços de e-mail da sua conta do GitHub. Pedimos ao GitHub apenas `read:user` e `user:email`: nunca obtemos acesso aos seus repositórios, privados ou públicos, por meio da sua conta. Não guardamos seu token de acesso do GitHub depois do login. Precisamos disso para criar sua conta e reconhecer você na próxima vez (execução do nosso acordo com você). O seu login do GitHub é atualizado a cada entrada, então o seu perfil sempre leva à sua conta atual do GitHub.

**Seu perfil.** Nome de usuário, nome de exibição, bio, site e idioma. O nome e a bio começam com os seus valores do GitHub; você pode alterá-los em Configurações. Seu nome de usuário, nome de exibição, bio, site, login do GitHub e o mês em que você entrou são **públicos**.

**Seu endereço de e-mail.** É guardado com a sua conta e visível apenas para a nossa equipe. Nunca é exibido no site. O site não envia e-mails; usaríamos o endereço apenas para falar com você sobre a conta ou uma denúncia.

**Seus projetos.** Tudo o que você preenche: nome, slogan, descrição, links, tags, as ferramentas de IA que você diz ter usado (exibidas como declaradas pelo autor), capturas de tela e entradas do diário de desenvolvimento. Projetos publicados são públicos; rascunhos só são visíveis para você e para a nossa equipe. As capturas de tela são recodificadas no envio, o que remove metadados ocultos, como dados da câmera ou localização por GPS.

**Verificações de comprovação.** Para conceder selos, verificamos os fatos nós mesmos (nosso interesse legítimo em mostrar comprovações confiáveis):

- *Repo owner:* consultamos a API pública do GitHub sobre o repositório que você vincula e guardamos o id dele, o id da conta dona, se ele é seu, a data de criação e o campo Website, o primeiro commit do histórico (id e data), o seu número de commits, as datas do seu primeiro e último commit, o número de semanas com commits seus e o estado de uma revisão manual, quando for necessária. Verificamos de novo toda semana. A lista de outras pessoas que contribuem é lida durante a verificação e não é guardada. Se você usa o arquivo de verificação em um repositório de organização, também guardamos se ele foi encontrado.
- *Live:* consultamos os registros DNS do domínio do seu projeto ou acessamos a página dele para encontrar seu token de verificação.
- *Steady:* acessamos o endereço do seu projeto a cada poucas horas e guardamos se ele respondeu e com que rapidez. Essas verificações ficam guardadas por **90 dias**.

Os resultados aparecem na página pública do seu projeto.

**Quem você segue e curtidas.** Guardamos quem você segue e quais projetos você curtiu. Os outros veem apenas os totais, não as listas.

**Denúncias.** Se você denunciar um projeto ou um perfil, guardamos o motivo e os detalhes que você escrever. Só a nossa equipe vê as denúncias. A pessoa denunciada não é informada de quem a denunciou.

**Aceite dos Termos.** Guardamos qual versão dos Termos você aceitou e quando.

**Registro de auditoria.** Mantemos um registro interno de mudanças de selos, ações de moderação e exclusões de contas, para que as decisões possam ser conferidas depois. Só a nossa equipe pode vê-lo.

**Endereços IP e registros.** O aplicativo não guarda seu endereço IP, e os registros dele não o contêm. De cada requisição de página, os registros anotam apenas o método, o endereço da página (sem o que vem depois de um `?`), o status da resposta, o tamanho e o tempo gasto, além dos erros. Não há dados do seu navegador. Os endereços de página incluem nomes de usuário (`/u/<username>/`), então uma linha de registro pode mostrar qual perfil foi aberto, mas não por quem.

**Registro de erros.** Quando algo falha, o aplicativo grava uma entrada curta em um arquivo de erros no nosso servidor: a hora, um número de referência aleatório (o mesmo mostrado na página de erro), o método da requisição, o endereço da página sem o que vem depois de `?` e com nomes de usuário trocados por `[user]`, o status da resposta, a parte do código que falhou e a mensagem técnica, da qual são removidos endereços de e-mail, endereços IP e tudo o que pareça senha ou chave. Páginas não encontradas vão para um arquivo separado, cada endereço no máximo uma vez por minuto. Esses arquivos nunca contêm seu endereço IP, dados do navegador, cookies, o que você digita em formulários, seu e-mail nem seu nome de usuário. Cada arquivo é limitado a 5 MB mais 5 cópias anteriores; ao atingir o limite, a mais antiga é apagada.

> **TODO antes do lançamento:** o servidor web na frente do aplicativo mantém seu próprio registro de acessos, que por padrão inclui endereços IP. O que ele registra e por quanto tempo guarda (e por quanto tempo os registros do aplicativo são guardados) ainda não foi decidido. É preciso preencher isso, ou desativar o registro de IP, antes de esta página se tornar pública.

**Proteção contra abusos.** Para limitar abusos, contamos algumas ações (por exemplo, curtidas por hora) no banco de dados do site. Cada contador é um número ligado à sua conta ou a um projeto, sem endereço IP, e vale por no máximo 24 horas. Depois disso deixa de ser usado, mas a linha pode ficar no banco até ser limpa.

**Análise de uso e rastreamento.** Não há: nem análise de uso, nem publicidade, nem scripts de rastreamento. As fontes são servidas pelo nosso próprio servidor.

**Backups.** Todos os dias fazemos uma cópia do banco de dados e das capturas de tela enviadas e guardamos cada cópia por 14 dias. Se você excluir a conta, seus dados ficam nessas cópias até a última que os contém ser substituída, em até 14 dias.

## Por quanto tempo guardamos {#retention}

- Sua conta, perfil, projetos, quem você segue e curtidas: até você excluí-los ou excluir a conta.
- Verificações de disponibilidade: 90 dias.
- Sessões de login: 2 semanas, ou até você sair da conta.
- Denúncias que você fez: permanecem depois de tratadas. Se você excluir sua conta, ficam sem o seu nome.
- Registro de auditoria: é mantido. As entradas sobre uma conta excluída não contêm o nome de usuário nem o e-mail.
- Contadores de proteção contra abusos: no máximo 24 horas.
- Backups: 14 dias. Uma conta excluída some deles em até 14 dias.
- Arquivos do registro de erros: até encherem (5 MB mais 5 cópias anteriores de 5 MB), depois as entradas mais antigas são apagadas.
- Registros do servidor web e do aplicativo: **TODO**, ainda não decidido.

## Quem mais recebe dados {#recipients}

- **GitHub, Inc.** Você entra em github.com, e o nosso servidor lê seu perfil e dados públicos de repositórios pela API do GitHub. A declaração de privacidade do próprio GitHub vale para o seu uso do GitHub.
- **Os servidores do seu projeto.** Nas verificações de Live e Steady, o nosso servidor acessa o DNS do seu domínio e o endereço do seu projeto. Eles veem o nosso servidor, não você.
- **Nosso provedor de hospedagem**, que mantém o servidor e o banco de dados para nós.

Não vendemos seus dados nem os compartilhamos para publicidade.

## Seus direitos {#rights}

- **Ver e baixar seus dados:** em Configurações → “Baixar meus dados” você recebe um arquivo JSON com seu perfil, dados do GitHub, projetos, diário de desenvolvimento, curtidas, quem você segue e as denúncias que fez.
- **Corrigi-los:** edite seu perfil em Configurações e seus projetos nas páginas deles.
- **Excluí-los:** Configurações → “Excluir conta”. Isso remove na hora seu perfil e todos os seus projetos, curtidas e quem você segue, e não pode ser desfeito. Seu nome de usuário fica livre.
- **Se opor ou reclamar:** escreva para [{{ contact_email }}](mailto:{{ contact_email }}). Se você mora na UE, no Reino Unido ou na Ucrânia, também pode reclamar à sua autoridade de proteção de dados.

## Cookies {#cookies}

Usamos apenas os cookies de que o site precisa para funcionar. Veja a [política de cookies](/legal/cookies/).

## Alterações {#changes}

Se esta política mudar, atualizamos a data no topo. Se a mudança for importante, pediremos que você aceite os Termos atualizados na sua próxima visita.
