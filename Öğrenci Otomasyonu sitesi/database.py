import sqlite3

#Veri tabani acma
conn = sqlite3.connect('database.db')

#Tablolari olusturma
conn.execute('''CREATE TABLE `kullanicilar` (
	`userId`	INTEGER,
	`parola`	TEXT,
	`email`	TEXT,
	`adi`	TEXT,
	`soyadi`	TEXT,
	`adres1`	TEXT,
	`adres2`	TEXT,
	`postaKodu`	TEXT,
	`il`	TEXT,
	`ilce`	TEXT,
	`ulke`	TEXT,
	`tel`	TEXT,
	`adminMi`	INTEGER,
	PRIMARY KEY(`userId`)
		)''')

conn.execute('''CREATE TABLE `dersler` (
	`lessonId`	INTEGER,
	`isim`	TEXT,
	`derssaati`	TIME,
	`aciklama`	TEXT,
	`resim`	TEXT,
	`kontejan`	INTEGER,
	`sinifId`	INTEGER,
	`ogretmenId`  INTEGER,
	FOREIGN KEY(`sinifId`) REFERENCES `siniflar`(`sinifId`),
	FOREIGN KEY(`ogretmenId`) REFERENCES `ogretmenler`(`ogretmenId`),
	PRIMARY KEY(`lessonId`)
		)''')

conn.execute('''CREATE TABLE `derssecimi` (
	`userId`	INTEGER,
	`lessonId`	INTEGER,
	FOREIGN KEY(`lessonId`) REFERENCES `dersler`(`lessonId`),
	FOREIGN KEY(`userId`) REFERENCES `kullanicilar`(`userId`)
		)''')

conn.execute('''CREATE TABLE `gecmis` (
	`userId`	INTEGER,
	`lessonId`	INTEGER,
	`tarih`	DATETIME,
	FOREIGN KEY(`userId`) REFERENCES `kullanicilar`,
	FOREIGN KEY(`lessonId`) REFERENCES `dersler`
		)''')


conn.execute('''CREATE TABLE `siniflar` (
	`sinifId`	INTEGER,
	`isim`	TEXT,
	PRIMARY KEY(`sinifId`)
		)''')
conn.execute('''CREATE TABLE `ogretmenler` (
	`ogretmenId`  INTEGER,
	`isim`	TEXT,
	PRIMARY KEY(`ogretmenId`)
		)''')



conn.commit()

#ilk veriler
cur = conn.cursor()	
cur.execute('''INSERT INTO siniflar (isim) VALUES ("deneme")''')
cur.execute('''INSERT INTO dersler (isim,derssaati,aciklama,resim,kontejan,sinifId) VALUES ("deneme","10", "deneme", "album1.jpg", "2", "1")''')
cur.execute('''INSERT INTO users (parola,email,adi,soyadi,adres1,adres2,ilce,postaKodu,il,ulke,tel,adminMi) 	VALUES ("deneme", "deneme@deneme.com", "deneme", "deneme","deneme",  "deneme", "deneme","deneme", "deneme", "deneme", "deneme", 1)''')

conn.commit()
conn.close()