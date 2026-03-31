V tej vaji boste morali izdelali preprosto simulacijo življenja, ki bo vsebovala plenilca, plen in hrano za plen (npr. **lisica, zajec, detelja**). Seveda bo potrebno izdelati teren na katerem se bodo lahko gibali in imeli možnost oziroma dostop do vira pitne vode. Za vajo boste imeli dva tedna časa. Bodite pozorni, saj se bo ta vaja uporabljala v nadaljnjih vajah. V tej fazi naj bo narejen MVP (**minimum viable product**).

## Razdelitev naloge po procentih:

### Do 60%

1. **Teren** sestavljen iz vode in kopnega
    - voda je neprehodna površina, kjer lahko bitja pijejo
    - kopno je prehodna površina, kjer iščejo hrano

2. **Štirje različni tereni**  
   – naj bo postavitev, oblika in razpršenost vode različna (reka, jezero, več jezer)

3. **Plenilec in plen** s sledečimi lastnostmi
    - **Lakota, žeja, razmnoževanje**  
      – te predstavljajo »kakovost« življenja in so med seboj povezane v določeno prioritetno vrsto.  
      Najpomembnejša za bitje je razmnoževanje, zato bo ob veliki želji za razmnoževanje prenehalo iskati vodo in hrano ter iskalo partnerja.  
      Naslednja je žeja, saj lahko brez hrane dlje preživi kot brez vode.  
      Bitje umre, ko mu zmanjka vode oziroma postane preveč žejno.  
      Če mu zmanjka hrane, se poveča potreba po vodi.

    - **Starost**  
      – uporablja se za omejitev življenjske dobe (št. ciklov ali časa) in za merjenje uspešnosti preživetja.

    - **Zaznava**  
      – območje, v katerem bitje zaznava svojo okolico.

    - **Spol**  
      – uporabljen pri razmnoževanju (potrebna sta dva različna spola).

    - **Hitrost in velikost**  
      – hitrost vpliva na žejo, velikost pa na potrebo po hrani.  
      Velikost vpliva tudi na izbiro partnerja (večje je boljše).

    - **Variacija / odstopanje**  
      – odstopanje od začetnih vrednosti (npr. ±10%).

---

### Do 10%

1. **Generiranje terena** s pomočjo Perlinovega šuma  
   (lahko uporabite knjižnico, vendar morate razumeti delovanje)

2. **Razdelitev terena** na 6 »višinskih pasov«
    - voda 40%
    - trava 35%
    - gozd 15%
    - pesek 2,5%
    - vrh gore 2,5%
    - gora 5%

   Teren je lahko predstavljen v 2D (barve) ali 3D (ne vpliva na oceno).

---

### Do 10%

## Lov in beg

1. **Plenilec**  
   – išče najprimernejši plen (bližji, počasnejši, večji) glede na potrebe.

2. **Plen**  
   – beži pred plenilci in izbira pot z najmanj plenilci.  
   Ne sme bežati iz enega plenilca direktno k drugemu.

---

### Do 5%

## Dedovanje in mutacija

1. Potomec naključno **deduje lastnosti** staršev  
   – dedovane lastnosti so osnova, na katero vpliva variacija.  
   (npr. večji starši → večji potomec, z odstopanjem)

2. **Mutacija**  
   – možnost spremembe lastnosti ob rojstvu  
   (npr. 10% verjetnost za ±20% spremembo)

---

### Do 15%

## Uporabniški vmesnik

Izdelava UI, ki omogoča:
- nastavljanje začetnih parametrov simulacije
- izbiro terena (1 od 4 ali generator)
- nastavljanje lastnosti bitij in mutacij
- premikanje po terenu (če je večji od prikaza)