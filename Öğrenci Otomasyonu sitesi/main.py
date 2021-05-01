from flask import *
from datetime import datetime 
import sqlite3, hashlib, os #hashlib sifreleme icin, os upload islemleri icin
from werkzeug.utils import secure_filename #dosya upload işlemleri için dahil edildi

app = Flask(__name__)
app.secret_key = 'random string' 
UPLOAD_FOLDER = 'static/uploads' #upload edilecek fotograflarin dosya konumu belirlendi
ALLOWED_EXTENSIONS = set(['jpeg', 'jpg', 'png', 'gif']) #upload edilecek fotograflarin uzantilari belirlendi
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def getLoginDetails():
    with sqlite3.connect('database.db') as conn: 
        cur = conn.cursor()
        if 'email' not in session: #emaile gore giris yapildi mi? yapilmadiysa alttaki satilar
            girildiMi = False #girilmedigi icin false
            adi = '' #sitede isim goruntulenmeyecek
            derssecimiSayac = 0 #dersseçimi icinde veri olmayacagi icin 0 belirlendi
        else: #giris yapildiysa alttaki satirlar
            girildiMi = True #giris yapildigi icin true
            cur.execute("SELECT userId, adi FROM kullanicilar WHERE email = ?", (session['email'], ))
            userId, adi = cur.fetchone() #yukaridaki sorgudan sirasiyla degiskenlere veri cekildi
            cur.execute("SELECT count(lessonId) FROM derssecimi WHERE userId = ?", (userId, ))
            derssecimiSayac = cur.fetchone()[0] #veritabanindaki dersseçimiteki itemlerin sayisi aktarildi
    conn.close() #connection kapatildi
    return (girildiMi, adi, derssecimiSayac) #fonksiyonun dondurdugu degiskenler


@app.route("/anasayfa")
def root():
    if 'email' not in session: #giris yapilmadiysa
        adminMi = 0 #admin mi degiskeni sifir olacak
        session['adminMi'] = adminMi #bu session icine aktarilacak
    adminpanel = '' #admin paneli goruntulenmemesi icin
    if session['adminMi'] == 0: #eger giris yapan kisi admin degilse
        adminpanel = 'display: none;' #bu kisiye admin paneli goruntulenmeyecek
    girildiMi, adi, derssecimiSayac = getLoginDetails() #yukarida olusturulan fonksiyondan degerler cekiliyor
    with sqlite3.connect('database.db') as conn:
        cur = conn.cursor()
        cur.execute('SELECT lessonId, isim, derssaati, aciklama, resim, kontejan,ogretmenId FROM dersler')
        dersVeri = cur.fetchall() #sql sorgusu ile cekilen veriler dersVeri'ye aktarilarak asagida html'ye gonderildi
        cur.execute('SELECT sinifId, isim FROM siniflar')
        sinifVeri = cur.fetchall() ##sql sorgusu ile cekilen veriler sinifVeri'ye aktarilarak asagida html'ye gonderildi
        cur.execute('SELECT ogretmenId, isim FROM ogretmenler')
        ogretmenVeri = cur.fetchall() ##sql sorgusu ile cekilen veriler ogretmenVeri'ye aktarilarak asagida html'ye gonderildi
    dersVeri = parse(dersVeri)   
    return render_template('anasayfa.html', adminpanel = adminpanel, dersVeri=dersVeri, girildiMi=girildiMi, adi=adi, 
    derssecimiSayac=derssecimiSayac, sinifVeri=sinifVeri,ogretmenVeri=ogretmenVeri)
@app.route("/AdminPanel")
def adminpanel():
    if session['adminMi'] == 1: #admin paneli eger admin mi degiskeni 1 ise goruntulenecek
        girildiMi, adi, derssecimiSayac = getLoginDetails() #login detaylari cekildi
        return render_template('AdminPanel.html' , girildiMi=girildiMi, adi=adi, derssecimiSayac=derssecimiSayac) 
    else:
        return "Bu sayfaya sadece adminler erisebilir..." #eger kisi admin degilse bu yazi ile karsilasacak

@app.route("/add")
def admin():
    if 'email' not in session: #bu kisim usttekilerle ayni mantik
        adminMi = 0
        session['adminMi'] = adminMi
    girildiMi, adi, derssecimiSayac = getLoginDetails()
    if session['adminMi'] == 1: #ekle sayfasi sadece adminlere goruntulenir
        with sqlite3.connect('database.db') as conn:
            cur = conn.cursor()
            cur.execute("SELECT sinifId, isim FROM siniflar")
            siniflar = cur.fetchall() #veritabanindan siniflar cekildi secme icin
            cur.execute("SELECT ogretmenId, isim FROM ogretmenler")
            ogretmenler = cur.fetchall() #veritabanindan ogretmenler cekildi secme icin
        conn.close()
        return render_template('ekle.html', siniflar=siniflar,ogretmenler=ogretmenler, girildiMi=girildiMi, adi=adi, derssecimiSayac=derssecimiSayac) #ekle.html'ye gonderildi
    else:
        return "Bu sayfaya sadece adminler erisebilir..."

@app.route("/addItem", methods=["GET", "POST"]) #ekle.html bu sayfayi cagirir ve veriler islenir
def addItem():
    if request.method == "POST":
        isim = request.form['isim']
        derssaati = float(request.form['derssaati'])
        aciklama = request.form['aciklama']
        sinifId = int(request.form['sinif'])
        kontejan = int(request.form['kontejan'])
        ogretmenId = int(request.form['ogretmen'])
        #Resim yukleme
        image = request.files['resim']
        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        imagename = filename
        with sqlite3.connect('database.db') as conn:
            try:
                cur = conn.cursor()
                cur.execute('''INSERT INTO dersler (isim, derssaati, aciklama, resim, kontejan, sinifId,ogretmenId) VALUES (?, ?, ?, ?, ?, ? ,?)'''
                , (isim, derssaati, aciklama, imagename, kontejan, sinifId,ogretmenId))            
                conn.commit() #yukarida html'den alinan veriler database'e aktarildi
                msg="Basarili"
            except:
                msg="Hata olustu"
                conn.rollback()
        conn.close()
        print(msg)
        return redirect(url_for('root'))#bu islem sonucunda anasayfaya yonlendirildi
    else:
        return redirect(url_for('root'))

@app.route("/addCategory") #sinif ekleme sayfasi
def addsinif():
    if 'email' not in session: #kisi admin degilse yapilacaklar
        adminMi = 0
        session['adminMi'] = adminMi 
    if session['adminMi'] == 1: #kisi adminse yapilacaklar
        girildiMi, adi, derssecimiSayac = getLoginDetails()
        return render_template('kategoriEkle.html' , girildiMi=girildiMi, adi=adi, derssecimiSayac=derssecimiSayac)
    else:
        return "Bu sayfaya sadece adminler erisebilir..."

@app.route("/addOgretmen") #ogretmen ekleme sayfasi
def addogretmen():
    if 'email' not in session: #kisi admin degilse yapilacaklar
        adminMi = 0
        session['adminMi'] = adminMi 
    if session['adminMi'] == 1: #kisi adminse yapilacaklar
        girildiMi, adi, derssecimiSayac = getLoginDetails()
        return render_template('ogretmenEkle.html' , girildiMi=girildiMi, adi=adi, derssecimiSayac=derssecimiSayac)
    else:
        return "Bu sayfaya sadece adminler erisebilir..."


@app.route("/addcategoryitem", methods=["GET", "POST"]) #sinifEkle.html icinden bu sayfa cagiriliyor
def addsinifitem():
    if request.method == "POST": 
        isim = request.form['isim']
        with sqlite3.connect('database.db') as conn:
            try:
                cur = conn.cursor()
                cur.execute('''INSERT INTO siniflar (isim) VALUES (?)''', (isim,))
                conn.commit() #burada sinif  veritabanina ekleniyor
                msg="Basarili"
            except:
                msg="Hata olustu"
                conn.rollback()
                return redirect(url_for('root'))
        conn.close()
        print(msg)
        return redirect(url_for('root'))
    else:
        return redirect(url_for('root'))

@app.route("/addogretmenitem", methods=["GET", "POST"]) #ogretmenEkle.html icinden bu sayfa cagiriliyor
def addogretmenitem():
    if request.method == "POST": 
        isim = request.form['isim']
        with sqlite3.connect('database.db') as conn:
            try:
                cur = conn.cursor()
                cur.execute('''INSERT INTO ogretmenler (isim) VALUES (?)''', (isim,))
                conn.commit() #burada ogretmen  veritabanina ekleniyor
                msg="Basarili"
            except:
                msg="Hata olustu"
                conn.rollback()
                return redirect(url_for('root'))
        conn.close()
        print(msg)
        return redirect(url_for('root'))
    else:
        return redirect(url_for('root'))

@app.route("/remove") #silme sayfasi
def remove():
    if session['adminMi'] ==1: #kisi admin ise
        with sqlite3.connect('database.db') as conn:
            cur = conn.cursor()
            cur.execute('SELECT lessonId, isim, derssaati, aciklama, resim, kontejan FROM dersler')
            data = cur.fetchall() #burada sayfada dersler goruntulenmek icin dataya atiliyor
        conn.close()
        return render_template('silme.html', data=data)
    else:
        return "Bu sayfaya sadece adminler erisebilir..."

@app.route("/removeItem") #silme.html'de silinmek istenen derse tiklandiginda bu sayfa cagirilir
def removeItem():
    if request.method == "GET" and session['adminMi']==1: #metod ve admin sartlari
        lessonId = request.args.get('lessonId')
        with sqlite3.connect('database.db') as conn:
            try:
                cur = conn.cursor()
                cur.execute('DELETE FROM dersler WHERE lessonID = ?', (lessonId, ))
                conn.commit() #lessonId'ye gore secilen ders veritabanindan silindi
                msg = "Silme basarili"
            except:
                conn.rollback()
                msg = "Hata olustu"
        conn.close()
        print(msg)
        return redirect(url_for('root'))
    else:
        return redirect(url_for('root'))

@app.route("/displayCategory") #sinif goruntuleme sayfasi
def displaysinif():
    if 'email' not in session: #giris yapilmadiysa
        adminMi = 0 #admin erisemesin
        session['adminMi'] = adminMi
    adminpanel = ''
    if session['adminMi'] == 0:
        adminpanel = 'display: none;' #admin paneli html icinde gorunmemesi icin
    if request.method == "GET":
        girildiMi, adi, derssecimiSayac = getLoginDetails()
        sinifId = request.args.get("sinifId") #secilen sinifin id alindi
        try:
            with sqlite3.connect('database.db') as conn:
                cur = conn.cursor()
                cur.execute("SELECT dersler.lessonId, dersler.isim, dersler.derssaati, dersler.resim, siniflar.isim FROM dersler, siniflar WHERE dersler.sinifId = siniflar.sinifId AND siniflar.sinifId = ?", (sinifId, ))
                data = cur.fetchall() #derslerin bilgileri alindi
                cur.execute('SELECT sinifId, isim FROM siniflar')
                sinifVeri = cur.fetchall() #bu id ile o sinifdaki butun dersler cekilecek
            conn.close()
            sinifAdi = data[0][4] 
            data = parse(data)
            return render_template('kategoriGrn.html', adminpanel=adminpanel, data=data, girildiMi=girildiMi, adi=adi, derssecimiSayac=derssecimiSayac, sinifAdi=sinifAdi, sinifVeri=sinifVeri)
        except:
            return redirect(url_for('root'))
    else:
        return redirect(url_for('root'))

@app.route("/account/profile") #profil sayfasi
def profileHome():
    if 'email' not in session: #bu kisim usttekilerle ayni mantik
        adminMi = 0
        session['adminMi'] = adminMi
    adminpanel = ''
    if session['adminMi'] == 0: #bu kisim usttekilerle ayni mantik
        adminpanel = 'display: none;'
    if 'email' not in session:
        return redirect(url_for('loginForm')) #giris yapilmadiysa login ekranina yonlendirme
    girildiMi, adi, derssecimiSayac = getLoginDetails() #giris yapildiysa detaylari cek ve html'ye aktar
    return render_template("profilSyf.html", adminpanel=adminpanel, girildiMi=girildiMi, adi=adi, derssecimiSayac=derssecimiSayac)

@app.route("/account/orders") #Ders seçimi Gecmisi Sayfasi
def orders():
    if 'email' not in session: #bu kisim usttekilerle ayni mantik
        adminMi = 0
        session['adminMi'] = adminMi
    adminpanel = ''
    if session['adminMi'] == 0: #bu kisim usttekilerle ayni mantik
        adminpanel = 'display: none;'
    if 'email' not in session:
        return redirect(url_for('loginForm')) #giris yapilmadiysa login sayfasina yonlendirme
    girildiMi, adi, derssecimiSayac = getLoginDetails()
    email = session['email']
    with sqlite3.connect('database.db') as conn:
        cur = conn.cursor()
        cur.execute("SELECT userId FROM kullanicilar WHERE email = ?", (email, ))
        userId = cur.fetchone()[0] #giris yapilan emaile gore kisinin userId'si cekildi
        cur.execute("SELECT dersler.lessonId, dersler.isim, dersler.derssaati, dersler.resim, gecmis.tarih FROM dersler, gecmis WHERE dersler.lessonId = gecmis.lessonId AND gecmis.userId = ?", (userId, ))
        dersler = cur.fetchall() #kisiye gore gecmisinde aldigi dersler ve bilgileri cekildi.
    toplamderssaati = 0
    for row in dersler:
        toplamderssaati += row[2] #gecmisinde aldigi derslerin toplam derssaati degiskene aktarildi
    toplamderssaati = round(toplamderssaati,2) #yuvarlama islemi icin
    return render_template("gecmis.html", adminpanel=adminpanel, dersler = dersler, toplamderssaati=toplamderssaati, girildiMi=girildiMi, adi=adi, derssecimiSayac=derssecimiSayac)

@app.route("/account/profile/edit") #profil bilgilerini duzenleme sayfasi
def editProfile():
    if 'email' not in session: #bu kisim usttekilerle ayni mantik
        adminMi = 0
        session['adminMi'] = adminMi
    adminpanel = ''
    if session['adminMi'] == 0: #bu kisim usttekilerle ayni mantik
        adminpanel = 'display: none;'
    if 'email' not in session:
        return redirect(url_for('loginForm')) #login ekranina yonlendirme
    girildiMi, adi, derssecimiSayac = getLoginDetails()
    with sqlite3.connect('database.db') as conn:
        cur = conn.cursor()
        cur.execute("SELECT userId, email, adi, soyadi, adres1, adres2, postaKodu, ilce, il, ulke, tel FROM kullanicilar WHERE email = ?", (session['email'], ))
        profilVeri = cur.fetchone() #kullanicinin emailine gore bilgileri degiskene aktarildi html'de duzenlenebilir
    conn.close()
    return render_template("profilDzn.html", adminpanel=adminpanel, profilVeri=profilVeri, girildiMi=girildiMi, adi=adi, derssecimiSayac=derssecimiSayac)

@app.route("/account/profile/view") #profil bilgilerini gorme sayfasi
def viewProfile():
    if 'email' not in session: #bu kisim usttekilerle ayni mantik
        adminMi = 0
        session['adminMi'] = adminMi
    adminpanel = ''
    if session['adminMi'] == 0: #bu kisim usttekilerle ayni mantik
        adminpanel = 'display: none;'
    if 'email' not in session: #bu kisim usttekilerle ayni mantik
        return redirect(url_for('loginForm'))
    girildiMi, adi, derssecimiSayac = getLoginDetails()
    with sqlite3.connect('database.db') as conn:
        cur = conn.cursor()
        cur.execute("SELECT userId, email, adi, soyadi, adres1, adres2, postaKodu, ilce, il, ulke, tel FROM kullanicilar WHERE email = ?", (session['email'], ))
        profilVeri = cur.fetchone() #kullanicinin emailine gore bilgileri degiskene aktarildi html'de gosterilecek
    conn.close()
    return render_template("profilGrn.html", adminpanel=adminpanel, profilVeri=profilVeri, girildiMi=girildiMi, adi=adi, derssecimiSayac=derssecimiSayac)

@app.route("/account/profile/changePassword", methods=["GET", "POST"])
def changePassword():
    if 'email' not in session: #bu kisim usttekilerle ayni mantik
        adminMi = 0
        session['adminMi'] = adminMi
    adminpanel = ''
    if session['adminMi'] == 0: #bu kisim usttekilerle ayni mantik
        adminpanel = 'display: none;'
    if 'email' not in session: #bu kisim usttekilerle ayni mantik
        return redirect(url_for('loginForm'))
    girildiMi, adi, derssecimiSayac = getLoginDetails()
    if request.method == "POST":
        eskiParola = request.form['eskiParola']
        eskiParola = hashlib.md5(eskiParola.encode()).hexdigest() #eski parola cozulerek degiskene aktarildi
        yeniParola = request.form['yeniParola']
        yeniParola = hashlib.md5(yeniParola.encode()).hexdigest() #yeni parola cozulerek degiskene aktarildi
        with sqlite3.connect('database.db') as conn:
            cur = conn.cursor()
            cur.execute("SELECT userId, parola FROM kullanicilar WHERE email = ?", (session['email'], ))
            userId, parola = cur.fetchone() #emaile gore userid ve parolasi alindi
            cur.execute("SELECT userId, email, adi, soyadi, adres1, adres2, postaKodu, ilce, il, ulke, tel FROM kullanicilar WHERE email = ?", (session['email'], ))
            profilVeri = cur.fetchone() # yine giris yapan kisinin emailine gore kisi bilgileri alindi
            if (parola == eskiParola):
                try:
                    cur.execute("UPDATE kullanicilar SET parola = ? WHERE userId = ?", (yeniParola, userId))
                    conn.commit() #yeni parola veritabanina aktarildi
                    msg="Sifre basariyla degistirildi."
                except:
                    conn.rollback()
                    msg = "Sifre degistirme basarisiz"
                return render_template("parolaDgs.html", msg=msg)
            else:
                msg = "Yanlis sifre"
            
        conn.close()
        return render_template("parolaDgs.html", adminpanel=adminpanel, profilVeri=profilVeri, girildiMi=girildiMi, adi=adi, derssecimiSayac=derssecimiSayac, msg=msg)
    else:
        return render_template("parolaDgs.html")

@app.route("/updateProfile", methods=["GET", "POST"]) #profilDzn.html icinden cagirilir
def updateProfile():
    if request.method == 'POST':
        email = request.form['email']
        adi = request.form['adi']
        soyadi = request.form['soyadi']
        adres1 = request.form['adres1']
        adres2 = request.form['adres2']
        postaKodu = request.form['postaKodu']
        ilce = request.form['ilce']
        il = request.form['il']
        ulke = request.form['ulke']
        tel = request.form['tel'] #html icinde doldurulan alanlar degiskenlere aktarildi
        with sqlite3.connect('database.db') as con:
                try:
                    cur = con.cursor()
                    cur.execute('UPDATE kullanicilar SET adi = ?, soyadi = ?, adres1 = ?, adres2 = ?, postaKodu = ?, ilce = ?, il = ?, ulke = ?, tel = ? WHERE email = ?', (adi, soyadi, adres1, adres2, postaKodu, ilce, il, ulke, tel, email))

                    con.commit()
                    msg = "Kayit basarili"
                except:
                    con.rollback()
                    msg = "Hata olustu"
        con.close()
        return redirect(url_for('root')) #islem sonucunda anasayfaya yonlendirme
    else:
        return redirect(url_for('root'))

@app.route("/") #giris sayfasi
def loginForm():
    if 'email' in session: #kullanici giris yaptiysa anasayfa ekranina yonlendirir
        return redirect(url_for('root'))
    else:
        return render_template('giris.html', error='')

@app.route("/login", methods = ['POST', 'GET']) #giris.html sayfasindan cagirilir
def login():
    if request.method == 'POST':
        adminMi = 0
        session['adminMi'] = adminMi
        email = request.form['email']
        parola = request.form['parola'] #email ve parola htmlden alinir
        if is_valid(email, parola, adminMi):
            session['email'] = email
            return redirect(url_for('root')) #giris yapildiginda anasayfaya yonlendirme
        else:
            error = 'Geçersiz kullanıcı adı veya şifre!'
            return render_template('giris.html', error=error)
    else:
        return redirect(url_for('loginForm')) #url'ye login yazilirsa loginForm'a yonlendirme

@app.route("/lessonDescription") #ders bilgileri sayfasi
def productDescription():
    try:
        if 'email' not in session: #bu kisim usttekilerle ayni mantik
            adminMi = 0
            session['adminMi'] = adminMi
        adminpanel = ''
        if session['adminMi'] == 0: #bu kisim usttekilerle ayni mantik
            adminpanel = 'display: none;'
        girildiMi, adi, derssecimiSayac = getLoginDetails()
        lessonId = request.args.get('lessonId')
        with sqlite3.connect('database.db') as conn:
            cur = conn.cursor()
            cur.execute('SELECT lessonId, isim, derssaati, aciklama, resim, kontejan,ogretmenId FROM dersler WHERE lessonId = ?', (lessonId, ))
            dersVeri = cur.fetchone() #dersler veritabanindan degiskene aktarildi
        conn.close()
        return render_template("dersBlg.html", adminpanel=adminpanel, data=dersVeri, girildiMi = girildiMi, adi = adi, derssecimiSayac = derssecimiSayac)
    except:
        return redirect(url_for('loginForm')) #giris yapilmadiysa login sayfasina yonlendirme

@app.route("/addToCart") #dersseçimi ekleme
def addToCart():

    try:
        if 'email' not in session: #bu kisim usttekilerle ayni mantik
            return redirect(url_for('loginForm'))
        else:
            lessonId = int(request.args.get('lessonId')) #dersseçimie aktarilmak uzere tiklanan dersin id'si
            with sqlite3.connect('database.db') as conn:
                cur = conn.cursor()
                cur.execute("SELECT userId FROM kullanicilar WHERE email = ?", (session['email'], ))
                userId = cur.fetchone()[0]
                try:

                    cur.execute("INSERT INTO derssecimi (userId, lessonId) VALUES (?, ?)", (userId, lessonId))
                    conn.commit() #userid'ye ait dersseçimie ders eklendi
                    msg = "Basarili"
                except:
                    conn.rollback()
                    msg = "Hata olustu"
            conn.close()
            return redirect(url_for('root'))
    except:
        return redirect(url_for('root'))
    


  
@app.route("/cart") #dersseçimi sayfasi
def cart():
    if 'email' not in session: #bu kisim usttekilerle ayni mantik
        adminMi = 0
        session['adminMi'] = adminMi
    adminpanel = ''
    if session['adminMi'] == 0: #bu kisim usttekilerle ayni mantik
        adminpanel = 'display: none;'
    if 'email' not in session: #bu kisim usttekilerle ayni mantik
        return redirect(url_for('loginForm'))
    girildiMi, adi, derssecimiSayac = getLoginDetails()
    email = session['email']
    with sqlite3.connect('database.db') as conn:
        cur = conn.cursor()
        cur.execute("SELECT userId FROM kullanicilar WHERE email = ?", (email, ))
        userId = cur.fetchone()[0] #yine giris yapilan emaile gore userId cekildi
        cur.execute("SELECT dersler.lessonId, dersler.isim, dersler.derssaati, dersler.resim FROM dersler, derssecimi WHERE dersler.lessonId = derssecimi.lessonId AND derssecimi.userId = ?", (userId, ))
        dersler = cur.fetchall() #cekilen bu userid'ye ait dersseçimiteki dersler cekildi
    toplamderssaati = 0
    for row in dersler: #bu kisim ustteki sayfa ile ayni mantikta
        toplamderssaati += row[2]
    toplamderssaati = round(toplamderssaati,2)
    return render_template("dersecimi.html", adminpanel=adminpanel, dersler = dersler, toplamderssaati=toplamderssaati, girildiMi=girildiMi, adi=adi, derssecimiSayac=derssecimiSayac)

@app.route("/removeFromCart") #dersseçimiten ders silme
def removeFromCart():
    if 'email' not in session: #bu kisim usttekilerle ayni mantik
        return redirect(url_for('loginForm'))
    email = session['email']
    lessonId = int(request.args.get('lessonId'))
    with sqlite3.connect('database.db') as conn:
        cur = conn.cursor()
        cur.execute("SELECT userId FROM kullanicilar WHERE email = ?", (email, ))
        userId = cur.fetchone()[0]  #bu kisim usttekilerle ayni mantik
        try:
            cur.execute("DELETE FROM derssecimi WHERE userId = ? AND lessonId = ?", (userId, lessonId))
            conn.commit() #userid'nin dersseçimiinde silinmek istenen ders silindi
            msg = "silme basarili"
        except:
            conn.rollback()
            msg = "Hata olustu"
    conn.close()
    return redirect(url_for('root'))

@app.route("/removeFromOrders") #ders seçimi gecmisini silme
def removeFromOrders():
    if 'email' not in session: #bu kisim usttekilerle ayni mantik
        return redirect(url_for('loginForm'))
    email = session['email']
    with sqlite3.connect('database.db') as conn:
        cur = conn.cursor()
        cur.execute("SELECT userId FROM kullanicilar WHERE email = ?", (email, ))
        userId = cur.fetchone()[0]  #bu kisim usttekilerle ayni mantik
        try:
            cur.execute("DELETE FROM gecmis WHERE gecmis.userId = ?", (userId, ))
            conn.commit() #giris yapan kisinin gecmisi silindi
            msg = "Her sey silindi"
        except:
            conn.rollback()
            msg = "Hata olustu"
    conn.close()
    return redirect(url_for('root'))

@app.route("/removeAllCart") #butun dersseçimini bosaltma 
def removeAllCart():
    if 'email' not in session:
        return redirect(url_for('loginForm'))
    email = session['email']
    with sqlite3.connect('database.db') as conn:
        cur = conn.cursor()
        cur.execute("SELECT userId FROM kullanicilar WHERE email = ?", (email, ))
        userId = cur.fetchone()[0]  #bu kisim usttekilerle ayni mantik
        try:
            cur.execute("DELETE FROM derssecimi WHERE derssecimi.userId = ?", (userId, ))
            conn.commit() #userid'ye gore dersseçimi bosaltildi.
            msg = "Her sey silindi"
        except:
            conn.rollback()
            msg = "Hata olustu"
    conn.close()
    return redirect(url_for('root'))

@app.route("/update") #ders guncelleme sayfasi
def updateitem1():
    if 'email' not in session: #bu kisim usttekilerle ayni mantik
        adminMi = 0
        session['adminMi'] = adminMi
    girildiMi, adi, derssecimiSayac = getLoginDetails()
    if session['adminMi'] ==1: #eger kisi adminse
        with sqlite3.connect('database.db') as conn:
            cur = conn.cursor()
            cur.execute("SELECT lessonId, isim FROM dersler")
            dersler = cur.fetchall() #derslerin isimleri cekildi guncelleme.html'ye gonderildi
        conn.close()
        return render_template('guncelleme.html', adminpanel=adminpanel, dersler=dersler, girildiMi=girildiMi, adi=adi, derssecimiSayac=derssecimiSayac)
    else:
        return "Bu sayfaya sadece adminler erisebilir..."

@app.route("/updateitem", methods=["GET", "POST"]) #guncelleme.html'den cagirildi
def updateitem2():
    if request.method == "POST":
        derslerId = request.form['dersler']
        yeniIsim = request.form['isim']
        yeniderssaati = request.form['derssaati'] #girilen yeni degerler degiskenlere aktarildi
        with sqlite3.connect('database.db') as conn:
            try:
                cur = conn.cursor()
                cur.execute("UPDATE dersler SET isim = ? , derssaati = ? WHERE lessonId = ?", (yeniIsim, yeniderssaati , derslerId))
                conn.commit() #veritabanina kaydedildi
                msg="Basarili"
            except:
                msg="Hata olustu"
                conn.rollback()
                return redirect(url_for('root'))
        conn.close()
        print(msg)
        return redirect(url_for('root'))
    else:
        return redirect(url_for('root'))


@app.route("/checkout") #ders alma
def checkout():
    if 'email' not in session: #bu kisim usttekilerle ayni mantik
        adminMi = 0
        session['adminMi'] = adminMi
    adminpanel = ''
    if session['adminMi'] == 0: #bu kisim usttekilerle ayni mantik
        adminpanel = 'display: none;'
    if 'email' not in session: #bu kisim usttekilerle ayni mantik
        return redirect(url_for('loginForm'))
    girildiMi, adi, derssecimiSayac = getLoginDetails()
    email = session['email']
    with sqlite3.connect('database.db') as conn:
        cur = conn.cursor()
        cur.execute("SELECT userId FROM kullanicilar WHERE email = ?", (email, ))
        userId = cur.fetchone()[0]  #bu kisim usttekilerle ayni mantik
        cur.execute("INSERT INTO gecmis (userId, lessonId, tarih) SELECT userId, lessonId , datetime('now','+3 hour') FROM derssecimi")
        dersler = cur.fetchall() #alinan ders dersseçimie aktarildi
        try:
            cur.execute("DELETE FROM derssecimi")
            conn.commit()
            msg = "Her sey silindi"
        except:
            conn.rollback()
            msg = "Hata olustu"  
    toplamderssaati = 0
    return render_template("dersAlma.html", adminpanel=adminpanel, dersler = dersler, toplamderssaati=toplamderssaati, girildiMi=girildiMi, adi=adi, derssecimiSayac=derssecimiSayac)


@app.route("/logout") #cikis ekrani
def logout():
    if 'email' not in session: #kisi eger giris yapmamissa anasayfaya yonlendirilir
        return redirect(url_for('root'))
    email = session['email']
    with sqlite3.connect('database.db') as conn:
        cur = conn.cursor()
        cur.execute("SELECT userId FROM kullanicilar WHERE email = ?", (email, ))
        userId = cur.fetchone()[0]  #bu kisim usttekilerle ayni mantik
        try:
            cur.execute("DELETE FROM derssecimi WHERE derssecimi.userId = ?", (userId, ))
            conn.commit() #cikis yaparken dersseçimii silme 
        except:
            conn.rollback()
    conn.close()
    session.pop('email', None) #giris yapan kisiyi hafizadan atma
    return redirect(url_for('root')) #anasayfaya donus

def is_valid(email, parola, adminMi): #email ve parola dogru mu kiyasi
    con = sqlite3.connect('database.db')
    cur = con.cursor()
    cur.execute('SELECT email, parola, adminMi FROM kullanicilar')
    data = cur.fetchall()
    for row in data:
        if row[0] == email and row[1] == hashlib.md5(parola.encode()).hexdigest():
            adminMi = row[2]
            session['adminMi'] = adminMi
            return True
    return False


@app.route("/register", methods = ['GET', 'POST']) #kaydol.html'den cagirilir
def register():
    if request.method == 'POST':
        parola = request.form['parola']
        email = request.form['email']
        adi = request.form['adi']
        soyadi = request.form['soyadi']
        adres1 = request.form['adres1']
        adres2 = request.form['adres2']
        postaKodu = request.form['postaKodu']
        ilce = request.form['ilce']
        il = request.form['il']
        ulke = request.form['ulke']
        tel = request.form['tel'] #html'de doldurulan alanlar degiskenlere aktarildi

        with sqlite3.connect('database.db') as con:
            try:
                cur = con.cursor()
                cur.execute('INSERT INTO kullanicilar (parola, email, adi, soyadi, adres1, adres2, postaKodu, ilce, il, ulke, tel, adminMi) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)', (hashlib.md5(parola.encode()).hexdigest(), email, adi, soyadi, adres1, adres2, postaKodu, ilce, il, ulke, tel))

                con.commit() #veritabanina kaydedildi

                msg = "Kayıt Başarılı"
            except:
                con.rollback()
                msg = "Hata olustu"
        con.close()
        return render_template("giris.html", error=msg)
    else:
        return redirect(url_for('root'))


@app.route("/registerationForm") #kaydolma sayfasi
def registrationForm():
    if 'email' not in session: #kisi giris yapmadiysa kaydol.html acilir
        return render_template("kaydol.html")
    else:
        return redirect(url_for('root')) #giris yaptiysa kaydolma sayfasi acilmaz anasayfaya yonlendirilir

def allowed_file(filename): #fotograf isimlerini duzenli hale getirmek icin
    return '.' in filename and \
            filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

def parse(data): #dersleri listelememizde kullandigimiz fonksiyon. birden fazla ayni satir olmasin diye yazildi
    ans = []
    i = 0
    while i < len(data):
        curr = []
        for j in range(7):
            if i >= len(data):
                break
            curr.append(data[i])
            i += 1
        ans.append(curr)
    return ans

if __name__ == '__main__':
    app.run(debug=True, host= '0.0.0.0') #0.0.0.0 localhostta açık sunmak için. Bilgisayarın ipsine 5000. porttan bağlanılıyor
