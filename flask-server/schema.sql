drop table if exists asist;
create table asist (
	id integer primary key autoincrement,
	datetime date not null,
	teacher text not null,
	signature text not null,
	list text not null
	);

-- -----------------------------------------------
-- | OTRO ESQUEMA PARA HACER UNICOS LOS ARCHIVOS |
-- -----------------------------------------------

-- drop table if exists asist;
-- create table asist (
-- 	datetime date not null,
-- 	teacher varchar(100) not null,
-- 	signature varchar(100) not null,
-- 	list varchar(1000),
--  primary key (datetime, teacher, signature)
-- 	);