# Reviewer decision для Release 2 в Utility GIS editor

Отвечаю как архитектор enterprise GIS для коммунальных и сетевых операторов, с фокусом на authoritative utility network, branch versioning и эксплуатационные workflow. Ниже — не пересказ вендорской роли “Reviewer” из готового продукта, а **рекомендуемая модель Release 2**, выведенная из исходного файла, где уже зафиксирован utility-сценарий с офисными редакторами, полевыми бригадами, branch versioning и reconcile/post, и из официальной доменной документации ArcGIS Utility Network и branch versioning. fileciteturn0file0 citeturn5view1turn9view0turn18view1

## Контекст и границы решения

В исходном файле Utility GIS editor трактуется не как обычный картографический CRUD, а как редактирование **авторитетной сетевой модели**, где критичны versioning, reconcile/post, офисно-полевой цикл и последствия для связности сети. Это важно, потому что reviewer в таком продукте должен принимать решение не “по геометрии как таковой”, а по тому, **можно ли доверить изменение authoritative state** после проверки diff, topology, trace impact и operational context. fileciteturn0file0 citeturn18view1turn26view0

Официальные документы Esri описывают механику branch versioning и utility network, но не вводят отдельную бизнес-роль Reviewer. Они прямо описывают, что named version создается под отдельную единицу работы, например work order или job; что reconcile нужен для обнаружения конфликтов между named version и default; что reviewer-like решение по конфликтам принимается в Conflicts view; и что post — это отдельная операция публикации в default, которая может потребовать повторного reconcile, если default изменился после предыдущего reconcile. Поэтому ниже я формулирую **policy для Release 2**, а не “как это уже жёстко задано в ArcGIS”. citeturn5view1turn8view1turn9view0turn9view1

## Какое решение нужно реализовать в Release 2

### Что именно уточняем

Для Release 2 я бы фиксировал не “conflict resolution” и не “routing/escalation” как главный объект, а **reviewer decision = approval of change package for post readiness**. Иначе говоря, Reviewer должен принимать решение по **пакету изменения**, а не только по одному техническому моменту. Conflict resolution — это частный подшаг внутри reconcile/post, routing/escalation — исключительный путь, а post gate — технический финальный контроль. Главная сущность решения должна звучать так: **“пакет изменений одобрен как корректный и готовый к post при текущем состоянии default”**. Это лучше всего соответствует branch workflow, где diff, reconcile/conflicts и post формально разделены. citeturn8view1turn9view0turn9view1turn6view3

### Чем отличается approve от ready to post

**Approve** и **“можно отправить на post”** лучше развести на два разных шага. Причина простая: в ArcGIS post — это отдельная операция, она необратима, и она может потребовать повторного reconcile, если default изменился после review/reconcile. Кроме того, если default переведен в protected, публиковать в него могут только version administrator или пользователи с повышенными правами. Значит, бизнес-решение “пакет верный” и техническое решение “его можно публиковать в default сейчас” — это не одно и то же. citeturn9view1turn6view3

Практически это означает такую модель состояний для Release 2: **Proposed by Editor → Reconciled against current default → Approved package → Post authorized → Posted**. Если между approval и post изменился default, появилась новая dirty area, error, invalid subnetwork или новый trace delta, состояние должно уходить в **Stale approval**, а не в post. citeturn9view1turn6view0turn10view3turn27view1

### Кто принимает решение для Normal, High и Critical

Для **Normal** я бы разрешил путь без индивидуального reviewer approval: если автоматические гейты пройдены, trace impact отсутствует либо безопасно нулевой, dirty areas очищены, ошибок нет, а пакет попадает в аудит и в очередь на выборочный контроль, то можно идти через **audit + sample review**. Это не противоречит branch versioning: обязательного Reviewer в платформенной механике нет, а контроль можно организовать через protected default, права на post и аудит. Но из-за необратимости post такой путь допустим только для низкорисковых изменений. citeturn6view3turn9view1turn25view2turn25view0

Для **High** Reviewer должен принимать **финальное решение по содержанию пакета**, а не просто подтверждать proposal Editor. Editor готовит пакет и предлагает решение, но именно Reviewer должен решить, принимать ли представление Current, вернуть ли на доработку или не допускать до post. Это соответствует логике Conflicts view, где кто-то должен выбрать сохраняемую репрезентацию данных после reconcile. citeturn8view1turn9view0

Для **Critical** нужен **dual control**. Моя рекомендация: техническое подтверждение делает профильный специалист по сети или utility-network admin, а финальным владельцем authoritative state является тот, кто имеет право публикации в default при protected access, то есть version administrator или эквивалентная административная роль. При разногласии post не выполняется; named version сохраняется, конфликт документируется, и решение уходит на эскалацию авторитетному владельцу default вместе с зафиксированными альтернативами и evidence. Это прямо следует из того, что protected default ограничивает право post, а изменения, связанные с subnetworks, terminal configurations и rules, часто лежат уже в зоне административной конфигурации сети. citeturn6view3turn9view1turn27view0turn27view1turn21view1

## Когда Reviewer подключается и что он должен видеть

### В какой момент Reviewer получает работу

Для Release 2 Reviewer должен получать пакет **после Editor proposal и после reconcile against current default**, но до post. Это оптимальная точка по двум причинам. Во-первых, только после reconcile видно, есть ли реальные конфликты с default и как выглядит Current vs Target vs Common Ancestor. Во-вторых, если Reviewer принимает решение на дореконсайленном пакете, оно быстро устаревает, потому что default может уже отличаться от того состояния, которое Reviewer фактически одобрил. citeturn8view1turn9view0turn20view0turn19view1

Если конфликтов нет, Reviewer все равно должен получать пакет **после локального технического gate**: после валидации topology по измененной области, после расчета trace/subnetwork impact и после формирования Differences view. Это нужно, потому что utility network explicitly предупреждает: без validation edits не отражаются в topology, а trace без Validate Consistency может вернуть неожиданные результаты. citeturn6view0turn6view1turn26view0

### Минимальный вход для reviewer decision

Минимальный вход я бы зафиксировал как **шесть обязательных элементов**, а не как произвольный набор полей. Это должен быть компактный change package:

- **work order или job context**: branch version в Esri прямо описывается как isolated unit of work, обычно work order или job; без этого reviewer не понимает, зачем вообще сделано изменение; citeturn5view1
- **diff**: список insert/update/delete и сравнение Current/Target/Common Ancestor из Differences view; без diff reviewer не видит, что именно меняется; citeturn20view0turn8view1
- **validation status**: dirty areas, errors, время последней validation, affected extent; без этого нельзя доверять topology-aware анализу; citeturn6view0turn6view1turn15view1
- **trace или subnetwork impact summary** для всего, что может менять traversability, isolation, upstream/downstream или статус subnetwork; citeturn26view0turn27view1turn10view3
- **history and authorship**: кто менял, когда, из какой версии, и что изменилось после последнего reconcile; branch history и dirty areas прямо поддерживают временной и авторский контекст; citeturn19view1turn6view0
- **evidence/comments** — не всегда обязательны, но обязательны для полевого утверждения факта, для safety/service-affecting changes и для случаев, когда diff сам по себе не объясняет мотив изменения. Источник аудита должен хранить кто, что, когда и с каким outcome решил. fileciteturn0file0 citeturn25view2turn25view0

### Что Reviewer должен увидеть первым

Чтобы Reviewer понял сетевое последствие **без открытия внешней GIS**, первый экран должен показывать факты в таком порядке.

Сначала — **business context**: work order, ветка, риск-класс, кто редактор, когда пакет последний раз reconciling/validated. Далее — **короткий diff-summary**: сколько insert/update/delete, какие классы/типы активов изменены, и есть ли изменения geometry, associations, network attributes или terminal configuration; именно эти категории имеют прямое влияние на dirty areas и topology freshness. Затем — **Current vs Target vs Common Ancestor** по каждой ключевой фиче и компактное geometry compare из Differences/Conflicts view. После этого — **network health block**: dirty areas, errors, subnetwork status. И только затем — **trace delta**: какие subnetworks или service path задеты, что изменилось в traversability, barriers, isolation/open valves, controllers, downstream impact. Такой порядок соответствует тому, как Esri показывает differences, conflicts и consistency state, и минимизирует необходимость “прыгать” в внешнюю карту ради базового решения. citeturn20view0turn8view1turn6view0turn6view1turn26view0turn27view1

## Что всегда блокирует post и когда нужна эскалация

### Conditions, которые всегда должны блокировать post

Для Release 2 я бы сделал **жесткий post gate**. Следующие условия должны блокировать post без исключений.

- **Невыполненный reconcile или новые изменения в default после reconcile.** Esri прямо указывает, что если между reconcile и post default изменился, нужно reconciling снова. citeturn9view1
- **Unreviewed conflicts.** Платформа позволяет автоматически разрулить их при post по ранее выбранной стратегии, но для controlled utility workflow это слишком рискованно; если конфликт не review-marked, post должен быть заблокирован. citeturn8view1turn9view1
- **Dirty areas в зоне предполагаемого сетевого эффекта.** Edits, не отраженные в topology, не считаются tracing/diagram operations, а Validate Consistency заставляет trace падать при dirty areas на пути. citeturn6view0turn26view0
- **Error dirty areas, network errors, invalid topology state.** Ошибки означают нарушение rules/restrictions и должны быть исправлены до доверенного post. citeturn15view1turn21view1turn21view3
- **Dirty или Invalid subnetwork в затронутом контуре.** Update Subnetwork требует отсутствия dirty areas на определяющих объектах, а invalid subnetworks игнорируются до исправления и повторной валидации. citeturn10view3turn27view1
- **Unresolved association diff**, если association меняет connectivity, containment или structural attachment и его последствия не провалидированы. Ассоциации создают dirty areas, влияют на trace results и могут сами быть источником ошибок. citeturn6view0turn21view3turn26view0
- **Unexpected trace impact** без явного согласованного rationale. Utility network специально предупреждает, что trace отвечает на вопросы о состоянии сети “at any moment”; если итоговая traversability изменилась неожиданно, это уже не косметическая правка. citeturn26view0turn18view1
- **Missing evidence** для полевых фактов, safety-related changes или service-impacting corrections. Это не платформенное ограничение Esri, а рекомендуемый control: без evidence невозможно реконструировать, почему authoritative state был изменен. fileciteturn0file0 citeturn25view2turn25view0

### Когда вернуть работу Editor, а когда звать профильного специалиста

**Возврат Editor** нужен, когда проблема носит характер неполного пакета или обычной доработки: отсутствует validation, не приложен trace summary, не закрыты dirty areas, не хватает evidence, diff неконсистентно описан, либо обнаружено исправимое расхождение, не требующее изменения сетевых правил или административной конфигурации. Это обычный editorial rework, а не domain escalation. citeturn6view0turn6view1turn20view0

**Обязательная эскалация профильному специалисту** нужна, когда вопрос уже вышел за пределы обычной редакторской правки: требуется создать или менять rule, изменяется terminal configuration/path, меняются субсетевые контроллеры, появляется unsupported containment/attachment relationship, либо trace/subnetwork effect влияет на service restoration, safety или границы subnetwork. В error guidance Esri такие случаи системно указывает как требующие rule/configuration-level вмешательства, часто с пометкой Admin. citeturn21view1turn21view3turn27view0turn27view1

### Как классифицировать trace change

Я не рекомендую правило **“любое изменение trace = Critical”**. Оно будет слишком шумным и быстро разрушит процесс. Правильнее считать **Critical только тот trace change, который меняет authoritative network behavior**, а именно затрагивает хотя бы один из следующих эффектов: affected service path, affected subnetwork, affected controllers, safety isolation logic, traversability/barriers, network-rule-dependent connectivity или внешние operational outputs вроде export subnetwork для OMS/asset systems. Utility network trace directly используется для isolation, upstream/downstream analysis и operational impact, а subnetworks являются топологически значимыми сущностями с explicit clean/dirty/invalid life cycle. citeturn18view1turn26view0turn27view1turn10view3

Из этого следует практическая шкала. Если trace delta есть, но он не меняет service/subnetwork/safety semantics и не связан с rule/terminal/controller logic, это может оставаться **High**. Если trace delta меняет хоть что-то из перечисленного выше, это уже **Critical**. Это — продуктовая рекомендация, но она прямо опирается на сетевую механику Esri. citeturn26view0turn27view0turn27view1

## Stale approval, repeat review и аудит

### Какие изменения делают approval stale

Для Release 2 approval должен считаться **stale** после любого изменения, которое меняет topology-aware смысл пакета или его отношение к default. В этот список должны входить:

- **geometry changes**;
- **associations**;
- **network attributes**;
- **terminal configuration / terminal path / from-to terminal values**;
- **изменение default после reconcile/approval**;
- **изменение validation result, dirty/error status, subnetwork status**.

Это не произвольный список: dirty areas создаются именно от geometry, network-attribute-related edits, associations и terminal configuration information; validation меняет trust level topology; а изменение default после reconcile требует повторного reconcile еще до post. citeturn6view0turn15view0turn21view0turn9view1turn27view1

Я бы **не делал stale** из чисто текстового comment-only update, если он не меняет evidence interpretation и не сопровождается новыми редакторскими действиями в данных. Иначе review будет “застревать” на бюрократии. Но если comment добавляет новый факт, который меняет risk interpretation, пакет должен перейти в repeat review. Это уже policy decision, а не требование платформы. citeturn25view0turn25view1

### Что должно попасть в audit

Audit для Release 2 должен позволять **восстановить цепочку решения**, а не просто факт “Approved/Rejected”. Минимальный состав записи я рекомендую такой:

- идентификаторы **work order / version / reconcile moment / approval moment / post moment**;
- **кто** предложил решение, кто review-утвердил, кто постил в default;
- **что** было изменено: diff summary, affected classes/assets, trace/subnetwork impact;
- **какое состояние было до и после**: validation status, dirty areas, errors, subnetwork status;
- **какие альтернативы были отвергнуты** и почему;
- **какое evidence** использовалось, включая snapshot или hash/URI на вложение;
- **stale events**: что именно сделало approval устаревшим;
- **final post outcome**: posted, blocked, returned, escalated, superseded.

Такой состав согласуется и с branch history, где доступны timestamped edits и version lineage, и с рекомендациями OWASP логировать “when, where, who and what”, а также target/action/outcome, чтобы сохранялся реконструируемый audit trail. citeturn19view1turn25view0turn25view1turn25view2

### Как делать repeat review после stale approval

Для repeat review я не рекомендую ни полный re-review “с нуля” всегда, ни чисто delta-only режим всегда. Лучший вариант для Release 2 — **delta-first with anchored baseline**: reviewer сначала видит **только delta после последнего approval**, но интерфейс обязан показывать baseline approved package и новую точку сравнения Current vs Target vs Common Ancestor по затронутым объектам. Esri уже даёт модели сравнения, где видно текущее состояние, target/default и common ancestor; это идеально ложится на repeat review. citeturn20view0turn8view1turn19view1

Практическое правило такое: если stale вызван чисто внешним изменением default и пакет сам не менялся, reviewer сначала смотрит **delta against last approved state** и итог после нового reconcile. Если stale вызван собственными новыми data edits пакета — geometry, association, network attribute, terminal/path, validation/subnetwork result — reviewer должен увидеть **и delta, и обновленную “сводку пакета целиком”**, потому что сетевой смысл уже мог измениться. citeturn9view1turn6view0turn15view0turn27view1

## Acceptance examples для Release 2

### Безопасный High change с финальным решением Reviewer

Editor создает named version под конкретный work order, меняет geometry и атрибуты одного сегмента, валидирует topology, получает чистый status без errors, reconcile-ит пакет с current default, differences view показывает ограниченный diff, а trace с Validate Consistency не меняет subnetwork/controller semantics и не создает unexpected isolation effect. Reviewer видит package summary, принимает **финальное решение approve package**, после чего post выполняется уполномоченной ролью. Acceptance criterion: пакет публикуется только если между approval и post не изменился default и не возникли новые dirty areas/errors. citeturn5view1turn20view0turn6view1turn26view0turn9view1

### Critical change с обязательной эскалацией

Editor меняет association или terminal/path на устройстве, после чего trace показывает изменение upstream/downstream behavior, а затронутый subnetwork становится Dirty или Invalid после update/validate. Reviewer не может принять пакет единолично: требуется подтверждение профильного специалиста или utility-network admin, потому что изменение затрагивает terminal configuration, controller logic, rule-dependent traversability или service path. Acceptance criterion: без dual approval и clean subnetwork state post невозможен. citeturn6view0turn21view0turn21view3turn27view0turn27view1turn10view3

### Stale approval и повторный review

Reviewer уже одобрил пакет, но до post кто-то опубликовал изменения в default или Editor после approval поправил geometry/network attribute. При post система возвращает необходимость нового reconcile, либо пакет получает новые dirty areas и меняет trace/validation result. Acceptance criterion: исходное approval помечается stale, reviewer получает delta-since-approval и обновленный package summary, а post остается заблокированным до repeat review. citeturn9view1turn6view0turn15view0turn20view0turn19view1

## Итоговая спецификация для Release 2

Если свести всё к короткой продуктовой формуле, то для Release 2 я бы зафиксировал такую норму: **Reviewer принимает решение по change package, а не по одиночному конфликту; это решение выдается после reconcile и после технического pre-review gate; approve и post authorization — два разных шага; Normal может идти через audit + sample review, High требует финального Reviewer decision, Critical требует dual control; любые topology-relevant изменения и любые изменения default после reconcile делают approval stale; repeat review должен быть delta-first, но с доступом к полной предыдущей approved baseline.** Эта схема максимально согласуется и с исходным utility use case, и с тем, как branch versioning и utility network реально работают в authoritative edit workflow. fileciteturn0file0 citeturn9view0turn9view1turn8view1turn6view0turn26view0turn27view1
