Cel oprogramowania
======
Oprogramowanie ma na celu usprawnienie obsługi klientów Pozarządowego Centrum Dostępu do Informacji Publicznej oraz zwiększenie efektywności wsparcia ze strony praktykantów i ekspertów zewnętrznych.
Powstałe narzędzie ma również dostarczać dane o charakterze ilościowym na temat zakresu udzielanego wsparcia, uwzględniając drogę mailowa, telefoniczną, ustną i szkoleniową.


Spis treści
=======

.. contents::

Grupy użytkowników
=======

Zidentyfikowano następujące kategorie użytkowników:

Zespół:

* Prawnik – osoba o pełnym dostępie do wszystkich danych zgromadzonych w systemie,
* Obserwator – osoby o dostępie do wybranych spraw wyłącznie na potrzeby jej obserwacji np. na potrzeby samokształcenia zespołu, specjalnego monitoringu,
* Wsparcie – osoba (praktykant, ekspert zewnętrzny) o dostępie do wybranych spraw na potrzeby realizacji określonych zadań w niej np. przygotowania pisma, ale bez możliwości kierowania sprawy do klienta,
* Wsparcie - wsparcie z możliwością samozatwierdzenie pisma i skierowanie go do klienta.
 
Osoba zewnętrzna:

* Klient – osoba o dostępie do własnych spraw na potrzeby archiwalne oraz sporządzania nowych podań.
Przez każdego w sprawie należy rozumieć osobę, która jest albo prawnikiem, albo w kontekście danej sprawy obserwatorem, praktykantem, klientem.

Patrz `Uprawnienia`_.

Podstawowy sposób pracy
=======

pomocy pisemnej
----------
#. **Klient** pisze e-mail na wydzielony adres e-mail / wypełnia formularz na stronie internetowej dołączając załączniki.
#. **System** rejestruje sprawę.
#. Jeżeli klient z nami wcześniej się nie kontaktował (identyfikacja na podstawie adresu e-mail)  – **system** tworzy konto i przesyła hasło do klienta.
#. **System** przypisuje sprawę do konta użytkownika-klienta.
#. **Klient** jest powiadamiany o sygnaturze sprawy i przesyłany link do akt sprawy.
#. **Prawnicy** dokonują wstępnego przeglądu sprawy wypełniając jeden formularz wykonując co najmniej jedno z poniższych:
   * udzielają odpowiedzi przesyłanej do każdego w sprawie na e-mail,
   * przypisują sprawę do praktykanta / obserwatora za powiadomieniem wszystkich wewnętrznych w sprawie,
   * sporządza notatki dostępnej dla wewnętrznych użytkowników,
   * ustala termin.
#. **Praktykant** sporządza projekt odpowiedzi / notatkę za powiadomieniem zespołu w sprawie.
#. * **System** powiadamia o upływie dead-line.
#. **Prawnik** zatwierdzają z komentarzem pismo praktykanta za powiadomieniem zespołu w sprawie.
#. **System** przesyła pismo do klienta.
#. **Prawnik** zamyka sprawę (na potrzeby organizacyjne).
#. **Klient** odpowiada na dowolne pismo z systemu.
#. **System** otwiera sprawę.
#. **System** przypisuje pismo do sprawy i powiadamia **Zespół** w sprawie.

Rejestracja porad
---------

Prawnicy mają moduł do rejestracji porad udzielanych w różnej formie. Powstałe narzędzie ma również dostarczać dane o charakterze ilościowym na temat zakresu udzielanego wsparcia, uwzględniając drogę mailowa, telefoniczną, ustną i szkoleniową.

Rejestr porad jest zasadniczo niezależny od zbioru spraw prowadzonych w systemie.
 
Zob. `Pozycja rejestru`_

Szczególne widoki
==========

Widok stanu spraw ``cases.views.cases.CaseListView``
---------------

Niniejszy widok będzie istotny dla monitorowania realizowanych zadań. 

Przedstawia podstawowe informacje w sprawie zgodnie z posiadanymi uprawnieniami m. in. numer sprawy, tytuł sprawy, zestawienie osób i ich charakteru w sprawie, liczbę odpowiedzi.

Jest zapewniona możliwość filtrowania po sprawach zamkniętych / otwartych i innych kryteriach. Dane można także sortować według tytułu, klienta, czasu od ostatniej odpowiedzi.

Obiekty
==========

Użytkownik ``users.models.User``
---------------

Obiekt powinien posiadać co najmniej następujące atrybuty:

* nazwę użytkownika
* adres (y) e-mail,
* hasło.

Winna być możliwość wyświetlenia przez:

* prawników – wszystkich spraw klienta,
* obserwatora, praktykanta, eksperta, klienta – wszystkich spraw zgodnie z kompetencjami.

Sprawa ```cases.models.Case```
------------------

Obiekt powinien posiadać co najmniej następujące atrybuty:

* relacje do tagów,
* relacje do klienta,
* numer sprawy,
* tytuł sprawy,
* zestawienie osób w sprawie,
* czas od ostatniej odpowiedzi,
* czas zamknięcia sprawy,
* status sprawy (zamknięta, otwarta).

Być może każda sprawa powinna mieć przypisanego tylko jednego prawnika prowadzącego, a pozostały nie będzie o niej powiadamiany już więcej. 

Tag
------------

Obiekt „Tag” powinien posiadać co najmniej następujące atrybuty:

* nazwa
* widoczny w zestawieniu spraw (tak, nie),
* styl.

Rekord
-----------

Abstrakcyjny obiekt nie wymagany, ale jeżeli będzie istnieć (wskazane, dalszy opis przyjmuje jego istnienie) to powinien przechowywać co najmniej następujące atrybuty:

* relacje do podania / terminu / alarmu itp.
* relacja do sprawy,
* data utworzenia,
* data ostatniej modyfikacji,
* autor.

Podanie
^^^^^^^

Obiekt „Podanie” grupy „Rekord” służy do przechowywania wpływających i wysyłanych e-maili.

Obiekt ten powinien przechowywać co najmniej następujące atrybuty:

* autor,
* załączniki (zaw. :nazwa pliku, odnośnik do pliku).
* treść podstawowa,
* notatka wewnętrzna,
* charakter (wewnętrzny, dla klienta),

Termin
^^^^^^

Obiekt „Termin” służy gromadzeniu informacji o upływających terminach w sprawach. Obiekt ten powinien zawierać dane w zakresie:

* data utworzenia i przez kogo
* dead-line,
* odwołanie i przez kogo.

Alarm
^^^^^^

Obiekt „Alarm” wytwarzany będzie automatycznie informując o przekroczeniu terminu. Obiekt ten powinien zawierać dane co najmniej w zakresie:

* relacja do terminu.

Uprawnienia
--------

Obiekt „Uprawnienia” służy do ustalenia uprawnień użytkownika w ramach konkretnej sprawy. Patrz →Grupy użytkowników.

Przypisanie danej osobie uprawnień automatycznie dodaje ją do grona osób obserwujących daną sprawę, z czego może się wypisać (model opt-out).

Patrz `Rozkład uprawnień <Uprawnienia>`_.

Pozycja rejestru
---------

Obiekt „Pozycja rejestru” służy do rejestracji porad udzielonych poza bezpośrednim obiegiem w systemie.
Obiekt ten powinien zawierać dane w zakresie:

* Tematy,
* Problemy - anonimizacja, bezczynność, BIP, re-use itd., 
* Obszar geograficzny - UE, centralny, region (województwa),
* Typ osoby,
* Typ podmiotu zobowiązanego - ograniczone z istniejącego systemu,
* Kto udzielił porady,
* Data rejestracji,
* Notatki

Winna istnieć możliwość rejestracji zgłoszeń pozostawiając samą notatkę celem późniejszego uporządkowania.P
