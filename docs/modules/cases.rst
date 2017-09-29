Cases - rejestr spraw
=====================

W celu zrozumienia używanych określeń użytkowników zapoznaj się z :doc:`/modules/users`

Podstawowy przepływ pracy
-------------------------

1. Wniesienie sprawy za pomocą poczty elektronicznej
####################################################

**Klient** wypełnia formularz na stronie internetowej. Ma możliwość dołączyć załączniki. Jeżeli użytkownik nie jest zalogowany - ma możliwość podać adres e-mail.

.. _rejestracja-sprawy:

2. Rejestracja sprawy
#####################

Sprawa jest rejestrowana w systemie. O jej utworzeniu zostają powiadomieni administratorzy. Nadany zostaje unikalny numer.

3. Przypisanie sprawy
#####################

**Sekretariat** dokonuje wstępnego przeglądu sprawy przypisując sprawę do praktykanta / obserwatora za powiadomieniem wszystkich wewnętrznych w sprawie, a także ustala oznacza ewentualny termin.

.. _projekt-pisma:

4. Przygotowanie projektu pisma
###############################

**Wsparcie** sporządza projekt odpowiedzi w sprawie. O jej nadesłaniu powiadomiony zostaje każdy członek zaangażowany w sprawę.

5. Zatwierdzenie pisma
######################

**Prawnik** zatwierdzają pismo. Ma możliwość przedstawić uwagi do pisma. O akceptacji i uwagach powiadamiany jest każdy z zespołu zaangażowany w sprawę. Zatwierdzone pismo jest przesyłane do każdego zaangażowanego.

6. Zamykanie sprawy
####################

**Prawnik** zamyka sprawę, co ma charakter jedyny organizacyjny.

7. Odpowiedź na dowolną wiadomość
#################################

**Klient** ma możliwość w każdej chwili, aby odpowiadzieć na dowolne pismo z systemu. Skutkuje to otwarciem ponownie sprawy, a także powiadomieniem o nowym piśmie osoby, które dotychczas były zaangażowane w sprawe.

Alternatywny przepływ pracy
---------------------------

Wniesienie sprawy za pomocą poczty elektronicznej
#################################################

Klient ma możliwość wniesienia sprawy z wykorzystaniem dedykowanego adresu e-mail. Aplikacja na podstawie adresu e-mail przypisuje sprawę do konta użytkownika-klienta. **Klient** jest powiadamiany o numer sprawy i przesyłany jest mu link do akt sprawy. Następnie sprawa kontynuowana jest zgodnie z krokiem :ref:`rejestracja-sprawy`.

Wniesienie sprawy anonimowo
###########################

**Klient** wypełnia formularz na stronie internetowej. Ma możliwość dołączyć załączniki, a także obowiązek podać adres e-mail. Podany adres e-mail to jest on wykorzystywany do utworzenia konta użytkownika. Nazwa użytkownika jest generowana automatycznie na podstawie adresu e-mail. Hasło jest losowe. Dane te są przesyłane do użytkownika. Następnie sprawa kontynuowana jest zgodnie z krokiem :ref:`rejestracja-sprawy`.

Odrzucenie projektu pisma
#########################

Jeżeli prawnik nie akceptuje projektu pisma przedstawionego przez wolontariusza ma możliwość napisania uwag, które będą dostępne tylko dla członków zespołu. Następnie sprawa powraca do kroku :ref:`projekt-pisma`.

Odpowiedź e-mailowa
#######################

Na każde nadesłane pismo w sprawie każdy ma możliwość odpowiedzi, a odpowiedź jest rejestrowana w systemie. Odpowiedź - na podstawie adresu e-mail - jest identyfikowana i przypisywana do wolontariusza. Zamknięta sprawa jest otwierana. Następnie sprawa powraca do kroku :ref:`projekt-pisma`.

Status sprawy
-------------

Każda sprawa ma swój status, który może uleca następującej zmianie zgodnie z poniżej przedstawionym schematem.

.. digraph:: case_status

      "free" [label="wolna"];
      "assigned" [label="przypisana"];
      "closed" [label="zamknięta"];
      free -> assigned [label="przypisanie prawnika"];
      assigned -> free [label="usunięcie ostatniego prawnika"];
      assigned -> closed [label="zamknięcie sprawy"];
      free -> closed [label="zamknięcie sprawy"];
      closed -> free [label="nowe pismo do wcześniej wolnej sprawy"];
      closed -> assigned [label="nowe pismo do wcześniej przypisanej sprawy"]

Uprawnienia
-----------

Moduł w zakresie zarządzania kontrolą dostępu i użytkownikami wykorzystuje:

* uprawnienia, które mogą być lokalne, odnoszące się do konkretnej sprawy i globalne, które dotyczą całego systemu,
* flagi, które konfigurują zachowanie systemu wobec użytkownika,

Moduł wykorzystuje następujące uprawnienia umożliwiający określone akcje o sprecyzowanym zasięgu (domyślnie lokalnym):

* Może widzieć sprawę (```cases.can_view```) - oglądanie spraw, które jest globalne lub lokalne,
* Może nadawać nowe uprawnienia (```cases.can_assign```) - przypisywanie użytkowników do wolnej sprawy, które jest globalne lub lokalne,
* Może komunikować się z klientem (```cases.can_send_to_client```) - zatwierdzania pism, wysyłania pism bezpośrednio do klienta, a także jego obecność zmienia status sprawy na przypisana,
* Może nadawać uprawnienia (```cases.can_manage_permission```) - zarządzanie dowolnymi uprawnieniami w sprawie,
* Może dodawać wpisy (```cases.can_add_record```) - dodawać rekordy (listy, wydarzenia) w sprawie,
* Może zmieniać własne wpisy (```cases.can_change_own_record```) - edytować samodzielnie utworzone rekordy w sprawie,
* Może zmieniać wszystkie wpisy (```cases.can_change_all_record```) - edytować cudze rekordy w sprawie,
* Może zamknąć sprawę (```cases.can_close_case```) - oznaczyć sprawę jako zamkniętą,
* Może wybierać klienta (```cases.can_select_client```) - podczas tworzenia nowej sprawy przez WWW może sam wybrać klienta, które jest globalne,
* Może edytować sprawę (```cases.can_change_case```) - modyfikować tytuł sprawy i jej inne opcje.

Moduł wykorzystujące następujące flagi w edycji użytkownika:
* "W zespole" (``is_staff``), które określa czy użytkownik może oglądać projekty pism i wewnętrzną korespondencje w sprawie,
* "Powiadamiaj o nowej sprawie", które określa czy użytkownik ma być powiadamiany o nowych sprawach,
* "Powiadamiaj o listach w wolnych sprawach", które określa czy użytkownik ma być powiadamiany o listach w sprawach, które nie są przypisane.

W panelu administracyjnym podczas edycji użytkownika możliwe jest:

* zarządzanie uprawnieniami globalnymi,
* modyfikowanie flag użytkownika.

Zarządzanie uprawnieniami lokalnymi odbywa się z poziomu własnej sprawy.

Przykładowo, aby uzyskać użytkownika:

* widzi tylko przypisane do siebie sprawy (czyli jak zwykły członek zespołu), nie dostaje tych powiadomień o nowej sprawie, nie widzi spraw innych – wyłącznie nadać flagę "W zespole" dla użytkownika,
* widzi wszystkie sprawy, ale nie dostaje tych powiadomień o nowej sprawie należy nadać globalnie uprawnienie "Może widzieć sprawę",
* widzi wszystkie sprawy, otrzymuje powiadomienia o nowej sprawie oraz liście w sprawie nieprzypisanej należy nadać globalne uprawnienie "Może widzieć sprawę" oraz zmodyfikować flagę użytkownika "Powiadamiaj o nowej sprawie" oraz "Powiadamiaj o listach w wolnych sprawach".

Kod aplikacji
-------------

Widoki
######

.. automodule:: cases.views.cases
    :members:

.. automodule:: cases.views.permissions
    :members:


Model
######

.. automodule:: cases.models
    :members:


Formularze
##########
.. automodule:: cases.forms
    :members:

