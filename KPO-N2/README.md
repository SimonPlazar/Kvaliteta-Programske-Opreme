# Naloga 2 - Evolucioja agresije

V tej nalogi se bomo srečali s teorijo iger. Tako bomo znanje pridobljeno iz prejšnje vaje uporabili, za izvedbo te vaje. Potrebno bo malo prilagoditi delovanje in obnašanje bitij. Torej simulacija se bo začela podobno kot v prejšnji nalogi: na polje velikosti NxM postavimo poljubno število bitij. V tej nalogi se bodo bitja vedno pojavila na robu polja in se ne bodo naključno premikala. Bitja se bodo premikala do novega elementa simulacije. Namreč v simulacijo boste morali vključit hrano in za potrebe te naloge se bo hrana vedno pojavila v paru (dva 'kosa' hrane na enem mestu). Simulacija se bo izvajala po tako imenovanih generacijah in vsako od teh generacij se bo ponavljal isti postopek. Vsako generacij se na polju pojavi fiksno število parov hrane, vsako bitje se naključno postavi k hrani (samo dva bitja na par), bitja pojedo hrano in se vrnejo na rob. Seveda v takšni situaciji teorije iger ne moramo uvesti, saj potrebujemo vsaj dva tekmeca. Zato bomo ustvarili dva tipa bitij 'Miroljubno' in 'Agresivno' bitje ter še določili pravila kako se bodo bitja prehranjevala.

Pravila so sledeča:

Bitje nima prostega para hrane; Bitje ne preživi trenutne generacije;
Samo eno bitje najde par hrane; Bitje preživi in se razmnoži;
Srečata se dva miroljubna bitja; Oba preživita, se ne razmnožita;
Srečata se dva agresivna bitja; Oba umreta;
Srečata se agresivno in miroljubno bitje; Agresivno poje eno in pol hrane, tako preživi generacijo in ima 50% verjetnost razmnožitve, Miroljubno bitje poje samo pol hrane in ima tako 50% verjetnost preživetja

Tabela 1 Križna primerjava srečanj bitij

| / | Miroljubno | Agresivno |
|---|---|---|
| Miroljubno | 1,1 | ¼, ¾ |
| Agresivno | ¾, ¼ | 0,0 |

Vaša naloga je, da naredite aplikacijo z zgornjimi navodili. Dodatno pa morate s pomočjo grafa prikazati/ugotoviti, katero izmed bitij (agresivno ali miroljubno) ima boljšo verjetnost za preživetje. Ter prikaz scenarije na grafu, ki potrjujejo vašo ugotovitev.