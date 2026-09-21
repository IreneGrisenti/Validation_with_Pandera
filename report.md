# Rapport

## Syfte
Syftet med detta projekt var att lära mig grunderna i Pandera, hur det kan användas för schemabaserad datavalidering och hur validering kan integreras som ett steg i en datapipeline.  
Jag ville förstå hur ett schema definieras, vilka typer av kontroller som kan tillämpas på kolumner och hela dataframe, samt vad som händer när valideringen misslyckas. 


## Området och dess relevans
Området jag har fördjupat mig i är datavalidering med fokus på Pandera. Datavalidering handlar om att säkerställa att data har rätt struktur, typ och värden innan den används i analyser eller modeller. Detta är centralt för Data Science-yrkesrollen eftersom felaktig eller inkonsekvent data snabbt kan leda till felaktiga analyser, missvisande resultat och dåliga beslutsunderlag. Genom att bygga in validering tidigt i ett dataflöde kan man upptäcka problem innan de sprider sig vidare.


## Viktiga begrepp
- Ett **schema** fungerar som ett kontrakt som beskriver hur data förväntas se ut, till exempel vilka kolumner som ska finnas och vilken datatyp de ska ha och vilka värden som är tillåtna.  
- I Pandera definieras scheman antingen objektbaserat med **DataFrameSchema** eller klassbaserat med **DataFrameModel**.  
- En **Check** är en regel som tillämpas på en kolumn eller på hela dataframe, till exempel att ett värde måste vara positivt eller att två kolumner måste stämma mot varandra.  
- Med **coerce=True** kan Pandera konvertera värden till rätt datatyp innan valideringen sker.  
- **nullable=True** styr om saknade värden är tillåtna i en kolumn.  
- Vid **lazy validation** samlas alla validerings fel ihop och rapporteras samtidigt som en **error report** (ett **SchemaErrors**-objekt), istället för att valideringen stoppar vid det första felet.  
- Pandera erbjuder även dekoratorer som **check_input** och **check_output**, som gör det möjligt att integrera validering direkt i pipelinefunktioner så att data kontrolleras automatiskt.


## Genomförande
Projektet byggdes med Python, Pandas och Pandera, i en Jupyter-notebook för utforskningen och som fristående skript för proof of concept-delen.  

Eftersom riktig e-postkampanjdata inte var tillgänglig, skapade jag en syntetisk dataframe med 100 rader, där 30% av raderna medvetet innehåller fel. Vilka fel som injicerats loggades separat för att kunna jämföra med vad Pandera faktiskt fångade.  

Jag valde att arbeta med den objektbaserade **DataFrameSchema** istället för DataFrameModel eftersom projektet är litet och DataFrameSchema kändes mer grundläggande att förstå innan man går vidare till en klassbaserad lösning.  

Schemat definierar kontroller per varje kolumn och kontroller som jämför flera kolumner. Valideringen är integrerad som ett steg i pipelinen: funktionen `load_raw()` som läser in CSV-filen är dekorerad med `check_output`, så att data valideras automatiskt direkt när den lämnar funktionen.  

```python
@pa.check_output(raw_data_schema, lazy=True)
def load_raw(path: str) -> pd.DataFrame:
    """Loads the raw CSV. Raises SchemaErrors if it doesn't match the schema requirements."""
    return pd.read_csv(path, encoding="utf-8")
```

Vid fel fångas `SchemaErrors` och `failure_cases` används för att bygga en läsbar rapport med orsak per rad.  
De felaktiga raderna loggas, tas bort, och den rensade datan valideras på nytt för att bekräfta att den nu är korrekt. 

Ett problem var att `transaction_id` kan vara saknat, men standardtypen för heltal i pandera tillåter inte null-värden. Jag löste det genom att använda `pd.Int64Dtype`.  
Ett annat problem uppstod med `bounced`. Om kolumnen valideras direkt som bool, tolkar Python nästan alla icke-tomma värden (inklusive felaktiga strängar) som True, vilket gör att ogiltiga värden smiter förbi valideringen. Jag valde därför att validera kolumnen som text och istället kontrollera att värdet är exakt "True" eller "False" med `isin()`.  
För `recipient_id`, `campaign_id` och `transaction_id` skrev jag egna funktioner som körs med `element_wise=True`. Det innebär att Pandera kör funktionen på ett värde i taget istället för på hela kolumnen samtidigt. Fördelen är att när valideringen misslyckas pekar felmeddelandet exakt ut vilken rad och vilket värde som orsakade felet, istället för att bara säga att kolumnen som helhet innehåller något ogiltigt.


## Resultat
Lösningen validerar den syntetiska data mot schemat i `validation_schema.py`. När `main.py` körs läses rådatan in och valideras med `lazy=True`, vilket samlar alla brutna regler istället för att stoppa vid det första felet.

Valideringen fångar **33 felaktiga rader**, inte 30 som man skulle förvänta sig utifrån de 30% felen. Anledningen är att rader med duplicerat `transaction_id` loggas båda gångerna de förekommer, eftersom det inte går att avgöra vilken av raderna som har det korrekta ID:t.  
De 33 felaktiga raderna skrivs till `output/rejected_rows_log.csv` tillsammans med en läsbar kolumn `rejection_reason`, som visar exakt vilken kontroll som misslyckades och vilket värde som orsakade felet, till exempel:

```python
23,Matthew Taylor,matthew.taylor23@sampleco.net,3,Offers tailored just for you,2026-08-05,,,False,23,2026-08-20,-59.41,"col: transaction_amount, broken check: is_valid_amount (got: -59.41)"
```

De 33 felaktiga raderna droppas och de **67 återstående raderna** skickas därefter igenom schemat en andra gång för att bekräfta att den rensade dataset nu klarar samtliga kontroller.  
Resultatet sparas i `output/validated_rows.csv` och terminalen läser:

```text
Starting validation of raw data.
33 of 100 rows failed validation.
Rejection log written to output/rejected_rows_log.csv
67 rows passed validation after dropping rejected.
Validated data written to output/validated_rows.csv
```


## Begränsningar och möjliga förbättringar
Lösningen är mycket enkel, vilket innebär att flera saker skulle kunna förbättras eller byggas ut. Jag valde till exempel att inte använda Parser för att städa data innan validering. Ett konkret exempel är `bounced`: istället för att validera den som text, hade jag kunnat använda en parser för att först standardisera värdena och sedan validera kolumnen korrekt som bool.  
Fler kontroller hade också kunnat läggas till, exempelvis en gräns för hur höga eller låga `transaction_amount`, eller en kontroll av att `send_date` inte ligger i framtiden. Jag valde att fokusera på ett mindre antal tydliga regler istället för att täcka alla tänkbara fall.  
Slutligen bygger hela lösningen på en syntetisk datset med kända, kontrollerade fel. Detta gjorde det enkelt att verifiera att schemat fungerade som tänkt, men riktig data hade sannolikt innehållit mer oväntade och komplexa felmönster, vilket hade krävt ett mer flexibelt eller utvecklat schema.


## Koppling till yrkesrollen
Schemabaserad datavalidering är direkt tillämpbart i en Data Scientist- eller dataanalytikerroll, särskilt i tidiga steg av en pipeline där data hämtas in från externa källor. Genom att definiera ett schema en gång kan samma regler återanvändas för att kontrollera nya dataleveranser, vilket minskar risken för att felaktig data smyger sig in i analyser eller modeller utan att någon märker det.  


## Självreflektion
### 1. Vad lärde du dig som du inte kunde innan?
Jag lärde mig hur automatiserad datavalidering fungerar i praktiken med Pandera. Specifikt lärde jag mig hur man kan definiera ett schema som kontrollerar både enskilda kolumner och relationer mellan flera kolumner samtidigt, hur man samlar upp alla fel i en error report och hur ett schema kan integreras i pipelinen. 

### 2. Vad var svårast att förstå eller genomföra?
Det svåraste var att förstå varför vissa valideringar inte fungerade som förväntat trots att koden såg korrekt ut, och även skillnaden mellan kolum-checks och element_wise=True-funktioner tog tid att reda ut.

### 3. Vilket tekniskt val är du mest nöjd med och varför?
Jag är mest nöjd med egna funktioner med element_wise=True för att validera ID-kolumnerna. Istället för ett generellt felmeddelande för hela kolumnen, pekar valideringen ut exakt vilket värde på vilken rad som är ogiltigt. 

### 4. Vad hade du gjort annorlunda om du började om?
Om jag började om hade jag lagt in Parser-funktionalitet från början. Att städa data innan validering hade gjort schemat mer robust. Jag hade också planerat pipelinen bättre från början, så att varje steg syns tydligare separat: inläsning av rådata, validering och avvisade rader, städning av data, och slutligen validering igen av den rensade dataset.

### 5. Vad skulle vara ett naturligt nästa steg om du fortsatte arbetet?
Ett naturligt nästa steg skulle vara att lägga till Parser-funktionalitet i schemat. Jag skulle också vilja bygga ut pipelinen så att varje steg blir tydligare separerat och lättare att följa. Det skulle vara intressant att testa lösningen på en större eller mer oförutsägbar dataset, för att se om schemat behöver bli mer flexibelt för att hantera felmönster som inte är kända i förväg.

### 6. Vilket betyg tycker du själv att arbetet motsvarar – G eller VG?
VG

### 7. Motivera din bedömning genom att koppla till kraven för G och VG nedan.
Arbetet uppfyller kraven för G genom att jag har valt och avgränsat ett relevant område, satt mig in i det via officiell dokumentation och kompletterande källor, samt byggt en fungerande prototyp som läser in data och validerar den.  
Koden är strukturerad i separata filer dokumenterad i en README med instruktioner för installation och körning.  

Utöver detta anser jag att arbetet visar den fördjupade förståelse som krävs för VG.
Jag förklarar inte bara att Pandera fungerar, utan hur och varför. Jag har gjort och motiverat egna tekniska val, resonerat kring lösningens begränsningar och möjliga förbättringar.


## Källor
Pandera documentation: https://pandera.readthedocs.io/en/stable/  
Statology: https://www.statology.org/data-validation-in-python-with-pandera-a-practical-introduction/  
Python Data Bench: https://pythondatabench.com/article/data-validation-python-pandera-practical-guide  
Medium: https://medium.com/towards-artificial-intelligence/your-model-is-fine-your-data-isnt-dataframe-validation-with-pandera-1552c0daeeaf  