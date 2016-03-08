Cases
======

W celu zrozumienia używanych określeń użytkowników zapoznaj się z `modules/users.rst`_

Podstawowy schemat pracy
------------------------

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
#. **System** powiadamia o upływie dead-line.
#. **Prawnik** zatwierdzają z komentarzem pismo praktykanta za powiadomieniem zespołu w sprawie.
#. **System** przesyła pismo do klienta.
#. **Prawnik** zamyka sprawę (na potrzeby organizacyjne).
#. **Klient** odpowiada na dowolne pismo z systemu.
#. **System** otwiera sprawę.
#. **System** przypisuje pismo do sprawy i powiadamia **Zespół** w sprawie.


Views
-----
.. automodule:: cases.views.cases
    :members:
    
.. automodule:: cases.views.permissions
    :members:

Models
------
.. automodule:: cases.models
    :members:
    

Forms
-----
.. automodule:: cases.forms
    :members:
    
