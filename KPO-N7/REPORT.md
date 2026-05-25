## Zbrani podatki in relevanca

- Populacije (skupaj, prey, predator, clover) skozi cas: pokaže stabilnost in ravnotezje ekosistema.
- Rojstva po tipu: merijo uspešnost reprodukcije ter ali se populacije obnavljajo.
- Smrti po vzroku (zeja, starost, predacija, pojedeno): pokažejo, kateri mehanizmi so ozko grlo (voda, plenilci, hrana).
- Povprecna lakota/zeja po tipu: pove, ali so pogoji okolja primerni in ali so agenti stalno v stresu.
- Povprecne lastnosti (hitrost, velikost, vid) po tipu: pomagajo analizirati selekcijo in dinamiko genov.
- Povprecna starost po tipu: prikazuje zivljenjsko dobo populacije pri danih parametrih.
- Dropped frames (UI): omogoca primerjavo med simulacijo in UI ter identifikacijo ozkih grl prikaza.

## Frekvenca zajema

Podatki se agregirajo in zapisujejo vsakih `LOG_INTERVAL_TICKS` (privzeto 10) tickov. Tako je zajem dovolj pogost za analizo trendov, hkrati pa ne obremenjuje simulacije in ne vpliva na hitrost izvajanja.

## Izhodne datoteke

Ob vsakem zagonu simulacije se v mapi `logs` ustvarita:

- `logs/run_YYYYmmdd_HHMMSS.csv`: agregirani podatki za vsak interval.
- `logs/run_YYYYmmdd_HHMMSS.json`: metadata o zagonu (parametri, interval, trajanje, dropped rows v loggerju).

## CSV Analyzer App

Za hiter pregled CSV datotek je dodan UI analizator, ki prikaze:
- predogled prvih 200 vrstic,
- statistiko numericnih stolpcev (min, max, mean, std),
- podrobnosti izbranega stolpca.