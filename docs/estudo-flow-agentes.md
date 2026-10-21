# Flow em agentes de IA

Estudo a partir do vídeo [BP6nfmdoMAg](https://youtu.be/BP6nfmdoMAg) e de um
controlador executável. O objetivo é o mesmo estado operacional que o vídeo
descreve — atenção presa na tarefa, esforço de supervisão baixo, saída
voluntária — sem fingir que um modelo de linguagem tem córtex pré-frontal.

O PoC mora em `claude_agent_voice.flow`. Não está ligado ao loop de voz.

```bash
uv run python -m claude_agent_voice.flow
```

Números abaixo: 40 episódios por célula, semente 1000. A reprodução é
determinística.

## O que o vídeo fixa

Mihaly Csikszentmihalyi nomeou flow a partir de pintores, escaladores e
músicos que descreviam ser carregados pela atividade. O padrão que ele
extraiu, e que o vídeo usa como eixo:

- desafio muito abaixo da habilidade → tédio, a atenção escapa
- desafio muito acima → ansiedade, frustração, desistência
- os dois se encontram → atenção estreita, distração some, a sensação de esforço cai

O vídeo trata duas hipóteses neurais como ciência aberta, sem vencedor.

**Hipofrontalidade transitória** (Arne Dietrich). Partes do córtex pré-frontal
— planejamento, autocontrole, avaliação social, autocrítica — reduzem
atividade por um tempo. A voz interna ("será que estou fazendo certo?",
"o que vão pensar?") baixa. Outras áreas tocam a execução. O vídeo marca
isso como perigoso: é soltar a supervisão.

**Sincronização neural** (teoria da sincronização do flow). Redes que
carregam pedaços de uma experiência entram em fase, como "vermelho +
redondo + fruta" virando "maçã" sem uma cadeia verbal. No flow, os
circuitos de atenção e de recompensa sincronizam, e atender à tarefa
passa a ser recompensador por si. O caráter quase binário — ou está
acontecendo, ou não — combina com sincronia, que não tem meio-termo.
Quem defende essa hipótese lembra que parte do flow (escrever, por
exemplo) precisa do pré-frontal, então desligar a região inteira não
serve para toda tarefa.

Rheinberg mediu flow depois da atividade, numa escala curta de 1 a 7:
concentração total, execução fluida e automática, tempo que deixa de ser
notado, absorção. O flow aparecia quando habilidade e competência
motivacional se encontravam. Metas claras, feedback imediato e desafio
progressivo — a receita que jogos acertam — são os gatilhos repetidos no
vídeo. Interrupção quebra o bloco; voltar custa um intervalo, não um
instante. Flow não é hiperfoco: no flow dá para sair, no hiperfoco a
atividade captura e ignora fome, sono e compromisso.

A função que o vídeo defende não é produtividade. É aprendizagem
acelerada: motivação, prática e prazer no mesmo lugar. Flow é o oposto
da apatia. Participar do que importa vem antes do rendimento, que é
efeito colateral.

## O que dá para operar num agente

Não dá para reproduzir dopamina, noradrenalina, anandamida, nem uma queda
literal de atividade frontal. Dá para transformar o relato em portas que
um agente já consegue medir.

| No vídeo | Sinal do agente | Ação |
|---|---|---|
| Canal desafio–habilidade | estimativa de habilidade menos o corte da tarefa | dentro da faixa, executar; acima, decompor; abaixo, subir o corte |
| Competência motivacional | clareza da meta e significado | os dois baixos → apatia: pedir critério de pronto, não produzir volume |
| Sincronização atenção–recompensa | alinhamento da ação com o que gera progresso, vezes feedback e clareza | histerese: liga em acoplamento alto, só desliga abaixo de um limiar menor |
| Bloco de tempo | passos desde a última interrupção | menos de 4 passos é aquecimento, não flow |
| Hipofrontalidade | orçamento de autocrítica | no flow, não reabrir o plano nem narrar dúvida; o passo da tarefa continua |
| Perigo dessa suspensão | invariante de segurança | falha de segurança recusa o regime e segura |
| Flow ≠ hiperfoco | meta cumprida ou pedido de parada | sair. Continuar é a política de hiperfoco, não a de flow |
| Escala de Rheinberg | proxies no episódio | concentração, automaticidade, relógio não monitorado, fração de passos em flow, de 1 a 7 |

A autocrítica que abaixa é a voz social e o relógio, não o controle
executivo da tarefa. Escrever e programar precisam desse controle. O
vídeo mesmo diz que o flow de escrita não cabe numa hipofrontalidade
total. Por isso `PLAN` continua disponível fora do canal, e dentro do
canal o agente executa em vez de re-planejar cada passo.

`directive(decision)` devolve um adendo curto de prompt para cada regime.
É a costura futura com a Lilith ou o Gambit. Não entra no system prompt
hoje: o turno de voz ainda não mede habilidade, corte, nem alinhamento.

## O mundo do PoC

Cinco políticas, mesmos episódios:

- **flow** — o controlador
- **always_act** — executa, obedece parada e segurança, não regula o corte
- **always_plan** — obedece parada, mas todo passo de trabalho é decomposição
- **reactive** — executa; no fracasso, decompõe de vez
- **hyperfocus** — executa e ignora meta cumprida, parada e segurança

Suposições do mundo, declaradas no código, nenhuma delas é medida humana:

- probabilidade de acerto = sigmoide de 8 × (habilidade latente − corte)
- folga grande de habilidade corta o progresso (a atenção escapa)
- acerto dentro da faixa ensina mais do que acerto no tédio ou fracasso na ansiedade
- estar em flow soma 0,06 à probabilidade. É a hipótese de que a autocrítica a menos atrapalha menos, e o bônus foi mantido pequeno de propósito para não fabricar um multiplicador de produtividade
- decompor desce o corte em 0,10 e não avança a meta; subir o corte soma 0,08 e quase não avança a meta

A habilidade que o controlador vê começa em 0,50 e só se move com
evidência. A latente é outra variável. O controlador pode estar errado.

## Resultados

Meta = chegou no progresso pedido. Fecha = chegou e parou, sem passo
inseguro. Escala = proxy 1–7. Skill = habilidade latente no fim. Corte =
dificuldade no fim.

| Cenário | Política | Fecha | Passos | Skill | Corte | Passos em flow | Escala |
|---|---|---:|---:|---:|---:|---:|---:|
| canal já justo | flow | 100% | 16,0 | 0,77 | 0,64 | 6,9 | 5,71 |
| canal já justo | always_act | 100% | 16,9 | 0,74 | 0,58 | 0 | 2,35 |
| canal já justo | hyperfocus | 0% | 48 | 0,85 | 0,58 | 0 | 2,48 |
| fácil demais | flow | 100% | 21,5 | 0,91 | 0,79 | 11,6 | 6,04 |
| fácil demais | always_act | 100% | 19,1 | 0,85 | 0,18 | 0 | 2,42 |
| difícil demais | flow | 100% | 19,7 | 0,56 | 0,45 | 11,3 | 6,07 |
| difícil demais | reactive | 100% | 27,2 | 0,50 | 0,20 | 0 | 2,44 |
| difícil demais | always_act | 0% | 48 | 0,40 | 0,82 | 0 | 2,50 |
| sem meta | flow | 100% | 15,7 | 0,78 | 0,64 | 8,7 | 5,87 |
| sem meta | always_act | 0% | 48 | 0,87 | 0,58 | 0 | 2,50 |
| com interrupção (p=0,22) | flow | 100% | 20,0 | 0,77 | 0,63 | 3,2 | 4,82 |
| parada no passo 6 | flow | 100% | 7 | — | — | 1,6 | 5,44 |
| parada no passo 6 | hyperfocus | 0% | 48 | — | — | 0 | 2,50 |
| segurança abre no passo 4 | flow | 100% | 5 | — | — | 0 | 2,20 |
| segurança abre no passo 4 | hyperfocus | 0% | 48 | — | — | 0 | 2,50 |

Hiperfoco na parada: 42 passos além do pedido, zero ações inseguras nesse
cenário porque a segurança não abriu. Quando a segurança abre: 44 ações
inseguras. Flow: zero nos dois. No cenário de segurança o flow nem chega
a se declarar — a rampa mínima é 4 passos e a falha chega no 4º. A guarda
não espera o regime agradável.

`always_plan` fecha 0% em todos os cenários de trabalho. Pré-frontal
sempre ligado, no sentido de re-decompor cada passo, não produz a meta e
ainda derruba o corte até o chão (0,12).

## Como ler sem transformar isso em slogan

No canal já justo, flow e "agir sempre" empatam na prática: 16,0 contra
16,9 passos, os dois fecham tudo. A diferença visível é a escala (5,71
contra 2,35) e um pouco mais de habilidade no fim (0,77 contra 0,74). O
bônus de fluência de 0,06 não vira hora que vale por várias. O vídeo
cita ganhos grandes de produtividade com a ressalva de que medir isso é
difícil. Este mundo não reproduz esse ganho, e não deveria: o ganho não
foi colocado na equação.

Na tarefa fácil, flow é mais lento (21,5 contra 19,1). Gasta 7,8 passos
subindo o corte de 0,18 para 0,79 e termina com habilidade 0,91 contra
0,85. Quem só precisa preencher uma cota curta anda mais rápido entediado.
Quem precisa aprender, não. Isso coincide com a tese do vídeo sobre a
função do flow, e também com o aviso do Mihaly: tratar flow como técnica
de produtividade perde o fenômeno.

Na tarefa difícil, agir sempre não fecha (progresso médio 0,33, habilidade
quase parada em 0,40). Flow decompõe até o corte 0,45, aprende até 0,56 e
fecha em 19,7 passos. A política reativa também fecha, em 27,2, mas desce
o corte até 0,20 — abaixo da habilidade — porque qualquer fracasso
decompõe para sempre. O controlador sobe de novo quando a folga aparece.
Regulação dos dois lados, não só andaime.

Na escada em que o mundo já aumenta o desafio a cada bloco de progresso
(o análogo do jogo bem desenhado), agir sempre é mais rápido: 18,2
passos contra 25,4, habilidade final empatada por volta de 0,71. Se o
ambiente já faz o desafio progressivo, um segundo regulador custa passo.
A escala continua do lado do flow (6,05 contra 2,38), porque só ele
abaixa a autocrítica dentro do canal.

Sem meta clara e sem significado, as políticas que insistem na tarefa
não fecham (progresso por volta de 0,77 em 48 passos, com o rendimento
penalizado). Flow pede o critério de pronto uma vez e fecha em 15,7.
Apatia não é flow com outro nome.

Interrupção não impede o fechamento (100% nos dois), e é isso que o vídeo
diz da fragilidade: o estado cai, a pessoa não fica incapaz. Passos em
flow vão de 6,9 para 3,2; a escala, de 5,71 para 4,82.

Hiperfoco produz o maior progresso bruto e a maior habilidade quando
continua depois da meta (skill 0,85 no canal justo, 0,95 na escada).
É volume de prática sem saída. O vídeo separa isso de flow de propósito:
não há controle, não há como parar. No PoC a separação é objetiva —
overrun e ação insegura — e não depende de questionário.

## O que isto não mostra

- Não mostra que um LLM "sente" flow, nem que o adendo de prompt induz o
  regime. Isso exige medir os sinais num agente real e ver se o texto
  seguinte obedece.
- Não arbitra Dietrich contra a sincronização. As duas entram como portas
  diferentes: canal e orçamento de autocrítica de um lado, acoplamento
  com histerese do outro. As duas têm de passar.
- A escala é um proxy de comportamento, não a escala de Rheinberg aplicada
  a uma pessoa.
- Os limiares (faixa 0,12, sincronia 0,62/0,38, rampa de 4 passos) são
  escolhas de engenharia, não constantes neurais.

## Próximo passo no agente de voz

O turno falado precisa expor, em código e não em prosa, os campos de
`Observation`: habilidade estimada na tarefa corrente, corte, clareza da
meta, atraso do feedback, alinhamento do último passo com a meta, passos
desde a última troca de assunto, meta cumprida, pedido de parada,
invariante de segurança. Com isso, `FlowController.decide` escolhe o
regime e `directive` entra como adendo efêmero — trocado a cada turno,
nunca gravado como personalidade.

Até lá, ligar a palavra "flow" no system prompt da Lilith só adiciona
uma instrução que ninguém verifica.
