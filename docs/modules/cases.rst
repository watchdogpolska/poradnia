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

Każda ma swój status, który może uleca następującej zmianie zgodnie z stanem przedstawionym na

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

Kod aplikacji
-------------

Widoki
######

.. automodule:: poradnia.cases.views.cases
    :members:

.. automodule:: poradnia.cases.views.permissions
    :members:


Model
######

.. automodule:: poradnia.cases.models
    :members:


Formularze
##########
.. automodule:: poradnia.cases.forms
    :members:

