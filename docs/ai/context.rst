Kontekst Projektu
=================

Sieć Obywatelska Watchdog Polska
---------------------------------

Sieć Obywatelska Watchdog Polska to stowarzyszenie strażnicze założone w 2003 r. (pierwotna nazwa: Stowarzyszenie Liderów Lokalnych Grup Obywatelskich). Jego misją jest pilnowanie prawa obywateli do informacji — organizacja uczy, jak pytać instytucje publiczne, monitoruje realizację prawa do informacji i prowadzi postępowania sądowe, gdy to prawo jest naruszane.

Poradnia Prawna
---------------

Od 2009 r. SOWP prowadzi bezpłatną poradnię prawną, która od 2015 r. działa poprzez elektroniczny system helpdeskowy. Poradnia odpowiada osobom prywatnym, dziennikarzom, radnym czy organizacjom społecznym w sprawach dostępu do informacji publicznej i pokrewnych zagadnieniach.

Charakterystyka Problemów
-------------------------

Poradnia regularnie obsługuje zapytania dotyczące:

* Dostępu do informacji publicznej
* Ponownego wykorzystania informacji sektora publicznego
* Postępowań administracyjnych
* Skarg na bezczynność
* Odwołań od decyzji
* Tajemnicy przedsiębiorstwa w sektorze publicznym

Aktualne Wyzwania
-----------------

1. **Rosnąca liczba spraw** - zwiększa się liczba osób korzystających z poradni
2. **Powtarzalność pytań** - wiele spraw dotyczy podobnych problemów prawnych
3. **Czasochłonność** - każda odpowiedź wymaga analizy przepisów i precedensów
4. **Jakość odpowiedzi** - konieczność utrzymania wysokiego standardu prawnego
5. **Dostępność zasobów** - konieczność efektywnego wykorzystania bazy wiedzy
6. **Ograniczenia finansowe** - mogą wymagać ograniczenia zespołu, co przy utrzymaniu lub wzroście ilości spraw wymaga wzrostu efektywności

Obecna Infrastruktura
---------------------

System poradni zbudowany jest w oparciu o:

* **Django** - framework webowy w Pythonie
* **MySQL** - baza danych
* **Docker** - konteneryzacja

Ma architekturę typowego **Systemu helpdeskowego** - zarządzanie sprawami od 2015 r.

Struktura aplikacji obejmuje:

* `letters` - zarządzanie korespondencją
* `cases` - obsługa spraw
* `users` - zarządzanie użytkownikami

Potrzeba Wprowadzenia AI
------------------------

Implementacja sztucznej inteligencji ma na celu:

1. **Wsparcie prawników** w szybszym znajdowaniu relewantnych precedensów
2. **Przyspieszenie odpowiedzi** poprzez automatyczne sugerowanie źródeł
3. **Zwiększenie jakości** poprzez dostęp do pełnej bazy wiedzy
4. **Redukcję czasu** potrzebnego na przygotowanie standardowych odpowiedzi
5. **Usprawnienie procesów** wyszukiwania w istniejących materiałach

Ograniczenia i Wymagania
------------------------

**Zgodność z RODO**
   Wszystkie dane muszą być przetwarzane zgodnie z europejskimi przepisami o ochronie danych osobowych.

**Bezpieczeństwo**
   Dane wrażliwe muszą być odpowiednio zabezpieczone przed dostępem osób nieupoważnionych.

**Rezydencja danych**
   Wszystkie dane muszą pozostać w Europejskim Obszarze Gospodarczym (EOG).

**Niezawodność**
   System nie może zastąpić prawnika, ale ma służyć jako narzędzie wspomagające.
