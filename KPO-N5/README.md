# Naloga 5 - Čista kodas

V prejšnji nalogi smo si pripravili MVP simulacije življenja in s tem ogrodje katerega bom uporabili za predstavo različnih aspektov kvalitete programske opreme. Prav zaradi tega bo ta vaja namenjena izdelavi oziroma izboljšavi prejšnje naloge. Za ta namen boste dodelali manjkajoče funkcionalnosti in »počistili« vašo kodo.

Čiščenje kode oziroma bolje rečeno izboljšava berljivosti kode (ang. clean code) je zelo pomemben dale kakovosti programske opreme, saj lahko izboljša učinkovitost dela, ne le posameznika, temveč celotne ekipe. Pri tem se zmanjša stres, iskanje kode in se olajša vračanje in popravljanje kode v kasnejših terminih. Torej v tej nalogi boste vašo aplikacijo simulacijo življenja spremenili na način, ki ne bo spremenil delovanja, temveč bo izboljšala berljivost kode (ang. Refactoring https://refactoring.com/). Tako bomo podali določene smernice, ki vam bodo v pomoč pri pisanju čiste kode.

Smernice:

* smiselna imena spremenljivk, funkcij, razredov, itd.
  * konsistentna oblika poimenovanj
* »Koda, ki se sama komentira« (ang. Self.documenting code https://en.wikipedia.org/wiki/Self-documenting_code)
* konsistentna oblika kode
* samo en nivo zamika v desno
* izogibanje uporabe ključne besede else
* enkapsulacija primitivnih tipov, ki imajo specifično obnašanje
* primerno število vrstic razredov metod 
  * princip enojne odgovornosti (ang. Single-responsibility principle https://en.wikipedia.org/wiki/Single-responsibility_principle)  
* uporaba smo smiselnih komentarjev