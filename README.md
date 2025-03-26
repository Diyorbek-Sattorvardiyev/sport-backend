

---

### Umumiy so‘rovlar
1. **`/login`**  
   - **Metod**: `POST`  
   - **Tavsif**: Foydalanuvchi (admin, murabbiy yoki talaba) login va parol bilan autentifikatsiya qiladi. Muvaffaqiyatli bo‘lsa, JWT token qaytaradi.  
   - **Autentifikatsiya**: Yo‘q  

---

### Talabalar bilan ishlash (Students)
2. **`/students`**  
   - **Metod**: `GET`  
   - **Tavsif**: Barcha talabalarni ro‘yxatini olish (qidiruv parametri bilan).  
   - **Autentifikatsiya**: `token_required`  
   - **Rol**: `admin`  

3. **`/students`**  
   - **Metod**: `POST`  
   - **Tavsif**: Yangi talaba qo‘shish.  
   - **Autentifikatsiya**: `token_required`  
   - **Rol**: `admin`  

4. **`/students/<int:student_id>`**  
   - **Metod**: `PUT`  
   - **Tavsif**: Mavjud talaba ma’lumotlarini yangilash.  
   - **Autentifikatsiya**: `token_required`  
   - **Rol**: `admin`  

5. **`/students/<int:student_id>`**  
   - **Metod**: `DELETE`  
   - **Tavsif**: Talabani o‘chirish.  
   - **Autentifikatsiya**: `token_required`  
   - **Rol**: `admin`  

6. **`/students/view`**  
   - **Metod**: `GET`  
   - **Tavsif**: Talabalarni ko‘rish (admin va murabbiylar uchun).  
   - **Autentifikatsiya**: `token_required`  
   - **Rol**: `admin`, `coach`  

---

### Murabbiylar bilan ishlash (Coaches)
7. **`/coaches`**  
   - **Metod**: `GET`  
   - **Tavsif**: Barcha murabbiylarni ro‘yxatini olish (qidiruv parametri bilan).  
   - **Autentifikatsiya**: `token_required`  
   - **Rol**: `admin`  

8. **`/coaches`**  
   - **Metod**: `POST`  
   - **Tavsif**: Yangi murabbiy qo‘shish.  
   - **Autentifikatsiya**: `token_required`  
   - **Rol**: `admin`  

9. **`/coaches/<int:coach_id>`**  
   - **Metod**: `PUT`  
   - **Tavsif**: Mavjud murabbiy ma’lumotlarini yangilash.  
   - **Autentifikatsiya**: `token_required`  
   - **Rol**: `admin`  

10. **`/coaches/<int:coach_id>`**  
   - **Metod**: `DELETE`  
   - **Tavsif**: Murabbiy o‘chirish.  
   - **Autentifikatsiya**: `token_required`  
   - **Rol**: `admin`  

11. **`/coaches/view`**  
   - **Metod**: `GET`  
   - **Tavsif**: Murabbiylarni ko‘rish (barcha foydalanuvchilar uchun).  
   - **Autentifikatsiya**: `token_required`  
   - **Rol**: Har qanday rol (`admin`, `coach`, `student`)  

---

### Slayderlar bilan ishlash (Sliders)
12. **`/sliders`**  
   - **Metod**: `GET`  
   - **Tavsif**: Barcha slayderlarni ro‘yxatini olish.  
   - **Autentifikatsiya**: `token_required`  
   - **Rol**: Har qanday rol  

13. **`/sliders`**  
   - **Metod**: `POST`  
   - **Tavsif**: Yangi slayder qo‘shish (rasm bilan).  
   - **Autentifikatsiya**: `token_required`  
   - **Rol**: `admin`  

14. **`/sliders/<int:slider_id>`**  
   - **Metod**: `PUT`  
   - **Tavsif**: Slayder ma’lumotlarini yangilash (rasmni almashtirish imkoniyati bilan).  
   - **Autentifikatsiya**: `token_required`  
   - **Rol**: `admin`  

15. **`/sliders/<int:slider_id>`**  
   - **Metod**: `DELETE`  
   - **Tavsif**: Slayderni o‘chirish (rasm bilan birga).  
   - **Autentifikatsiya**: `token_required`  
   - **Rol**: `admin`  

---

### Yangiliklar bilan ishlash (News)
16. **`/news`**  
   - **Metod**: `GET`  
   - **Tavsif**: Barcha yangiliklarni ro‘yxatini olish (sana bo‘yicha tartiblangan).  
   - **Autentifikatsiya**: `token_required`  
   - **Rol**: Har qanday rol  

17. **`/news`**  
   - **Metod**: `POST`  
   - **Tavsif**: Yangi yangilik qo‘shish (bir nechta rasm bilan).  
   - **Autentifikatsiya**: `token_required`  
   - **Rol**: `admin`  

18. **`/news/<int:news_id>`**  
   - **Metod**: `PUT`  
   - **Tavsif**: Yangilikni yangilash (rasmlarni almashtirish yoki qo‘shish imkoniyati bilan).  
   - **Autentifikatsiya**: `token_required`  
   - **Rol**: `admin`  

19. **`/news/<int:news_id>`**  
   - **Metod**: `DELETE`  
   - **Tavsif**: Yangilikni o‘chirish (rasmlar bilan birga).  
   - **Autentifikatsiya**: `token_required`  
   - **Rol**: `admin`  

---

### Sport turlari bilan ishlash (Sport Types)
20. **`/sport-types`**  
   - **Metod**: `GET`  
   - **Tavsif**: Barcha sport turlarini ro‘yxatini olish.  
   - **Autentifikatsiya**: `token_required`  
   - **Rol**: Har qanday rol  

21. **`/sport-types`**  
   - **Metod**: `POST`  
   - **Tavsif**: Yangi sport turi qo‘shish (rasm bilan).  
   - **Autentifikatsiya**: `token_required`  
   - **Rol**: `admin`  

22. **`/sport-types/<int:sport_id>`**  
   - **Metod**: `PUT`  
   - **Tavsif**: Sport turini yangilash (rasmni almashtirish imkoniyati bilan).  
   - **Autentifikatsiya**: `token_required`  
   - **Rol**: `admin`  

23. **`/sport-types/<int:sport_id>`**  
   - **Metod**: `DELETE`  
   - **Tavsif**: Sport turini o‘chirish (rasm bilan birga).  
   - **Autentifikatsiya**: `token_required`  
   - **Rol**: `admin`  

---

### Mashg‘ulot jadvali bilan ishlash (Training Schedule)
24. **`/training-schedule`**  
   - **Metod**: `GET`  
   - **Tavsif**: Mashg‘ulot jadvalini ro‘yxatini olish (sana va vaqt bo‘yicha tartiblangan).  
   - **Autentifikatsiya**: `token_required`  
   - **Rol**: Har qanday rol  

25. **`/training-schedule`**  
   - **Metod**: `POST`  
   - **Tavsif**: Yangi mashg‘ulot jadvalini qo‘shish.  
   - **Autentifikatsiya**: `token_required`  
   - **Rol**: `admin`  

26. **`/training-schedule/<int:schedule_id>`**  
   - **Metod**: `PUT`  
   - **Tavsif**: Mashg‘ulot jadvalini yangilash.  
   - **Autentifikatsiya**: `token_required`  
   - **Rol**: `admin`  

27. **`/training-schedule/<int:schedule_id>`**  
   - **Metod**: `DELETE`  
   - **Tavsif**: Mashg‘ulot jadvalini o‘chirish.  
   - **Autentifikatsiya**: `token_required`  
   - **Rol**: `admin`  

---

### Natijalar bilan ishlash (Results)
28. **`/results`**  
   - **Metod**: `GET`  
   - **Tavsif**: Barcha natijalarni ro‘yxatini olish (sana bo‘yicha tartiblangan).  
   - **Autentifikatsiya**: `token_required`  
   - **Rol**: Har qanday rol  

29. **`/results`**  
   - **Metod**: `POST`  
   - **Tavsif**: Yangi natija qo‘shish (rasm bilan).  
   - **Autentifikatsiya**: `token_required`  
   - **Rol**: `admin`  

30. **`/results/<int:result_id>`**  
   - **Metod**: `PUT`  
   - **Tavsif**: Natijani yangilash (rasmni almashtirish imkoniyati bilan).  
   - **Autentifikatsiya**: `token_required`  
   - **Rol**: `admin`  

31. **`/results/<int:result_id>`**  
   - **Metod**: `DELETE`  
   - **Tavsif**: Natijani o‘chirish (rasm bilan birga).  
   - **Autentifikatsiya**: `token_required`  
   - **Rol**: `admin`  

---

### Foydalanuvchi profili bilan ishlash (Profile)
32. **`/profile`**  
   - **Metod**: `GET`  
   - **Tavsif**: Joriy foydalanuvchi profil ma’lumotlarini olish.  
   - **Autentifikatsiya**: `token_required`  
   - **Rol**: Har qanday rol  

33. **`/profile/update-password`**  
   - **Metod**: `PUT`  
   - **Tavsif**: Foydalanuvchi parolini yangilash.  
   - **Autentifikatsiya**: `token_required`  
   - **Rol**: Har qanday rol  

---

### Yuklangan fayllarni ko‘rsatish
34. **`/uploads/<path:filename>`**  
   - **Metod**: `GET`  
   - **Tavsif**: Yuklangan fayllarni (rasmlar va boshqalar) ko‘rsatish.  
   - **Autentifikatsiya**: Yo‘q  

---

### Eslatmalar
- **Autentifikatsiya**: `token_required` dekoratori ishlatilgan marshrutlar uchun HTTP sarlavhasida `Authorization: Bearer <token>` yuborilishi kerak.
- **Rol talablari**: `role_required` dekoratori bilan cheklangan marshrutlar faqat ko‘rsatilgan rollarga ega foydalanuvchilar uchun ishlaydi (`admin`, `coach`, `student`).
- **Ma’lumot formati**: Ko‘p hollarda JSON (`request.json`) yoki forma ma’lumotlari (`request.form`) qabul qilinadi, rasmlar esa `multipart/form-data` orqali yuboriladi.

Agar har bir marshrut uchun namunaviy so‘rovlar (masalan, `curl` bilan) yozishni xohlasangiz, menga xabar bering, men ularni alohida yozib beraman!
