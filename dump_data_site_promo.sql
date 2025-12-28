--
-- PostgreSQL database dump
--


-- Dumped from database version 17.7
-- Dumped by pg_dump version 17.7

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: abonnements; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.abonnements (
    id integer NOT NULL,
    client_id integer NOT NULL,
    plan character varying(50) NOT NULL,
    prix_mensuel numeric(10,2) NOT NULL,
    date_debut timestamp without time zone NOT NULL,
    date_fin timestamp without time zone,
    statut character varying(20),
    periode_essai boolean,
    date_fin_essai timestamp without time zone
);


--
-- Name: abonnements_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.abonnements_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: abonnements_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.abonnements_id_seq OWNED BY public.abonnements.id;


--
-- Name: clients; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.clients (
    id integer NOT NULL,
    nom character varying(100) NOT NULL,
    prenom character varying(100),
    entreprise character varying(100),
    email character varying(100) NOT NULL,
    telephone character varying(30),
    adresse text,
    ville character varying(100),
    code_postal character varying(10),
    date_creation timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: clients_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.clients_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: clients_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.clients_id_seq OWNED BY public.clients.id;


--
-- Name: abonnements id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.abonnements ALTER COLUMN id SET DEFAULT nextval('public.abonnements_id_seq'::regclass);


--
-- Name: clients id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.clients ALTER COLUMN id SET DEFAULT nextval('public.clients_id_seq'::regclass);


--
-- Data for Name: abonnements; Type: TABLE DATA; Schema: public; Owner: -
--

-- COPY public.abonnements (id, client_id, plan, prix_mensuel, date_debut, date_fin, statut, periode_essai, date_fin_essai) FROM stdin;
-- 4	3	essai	0.00	2025-12-21 19:40:48.770536	\N	actif	t	2026-01-20 19:40:48.770536
5	4	essai	0.00	2025-12-22 17:36:18.977662	\N	actif	t	2026-01-21 17:36:18.977662
INSERT INTO public.abonnements (id, client_id, plan, prix_mensuel, date_debut, date_fin, statut, periode_essai, date_fin_essai) VALUES
    (4, 3, 'essai', 0.00, '2025-12-21 19:40:48.770536', NULL, 'actif', TRUE, '2026-01-20 19:40:48.770536'),
    (5, 4, 'essai', 0.00, '2025-12-22 17:36:18.977662', NULL, 'actif', TRUE, '2026-01-21 17:36:18.977662');

-- COPY public.clients (id, nom, prenom, entreprise, email, telephone, adresse, ville, code_postal, date_creation) FROM stdin;
-- 1	Dupont	Jean	BTP Solutions	jean.dupont@email.com	0601020304	12 rue du BTP	Paris	75001	2025-12-21 17:49:07.063429
-- 2	Martin	Marie	Chantiers Express	marie.martin@email.com	0605060708	34 avenue des Travaux	Lyon	69000	2025-12-21 17:49:07.063429
-- 3	victoire	Frederic 	victoire	frederic.victoire@gmail.com	0689962910	\N	\N	\N	2025-12-21 19:31:24.533007
-- 4	test_nom	test_prenom	test_societe	test@gmail.com	0689962910	\N	\N	\N	2025-12-22 17:36:18.966731
INSERT INTO public.clients (id, nom, prenom, entreprise, email, telephone, adresse, ville, code_postal, date_creation) VALUES
    (1, 'Dupont', 'Jean', 'BTP Solutions', 'jean.dupont@email.com', '0601020304', '12 rue du BTP', 'Paris', '75001', '2025-12-21 17:49:07.063429'),
    (2, 'Martin', 'Marie', 'Chantiers Express', 'marie.martin@email.com', '0605060708', '34 avenue des Travaux', 'Lyon', '69000', '2025-12-21 17:49:07.063429'),
    (3, 'victoire', 'Frederic', 'victoire', 'frederic.victoire@gmail.com', '0689962910', NULL, NULL, NULL, '2025-12-21 19:31:24.533007'),
    (4, 'test_nom', 'test_prenom', 'test_societe', 'test@gmail.com', '0689962910', NULL, NULL, NULL, '2025-12-22 17:36:18.966731');


--
-- Name: clients_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.clients_id_seq', 4, true);


--
-- Name: abonnements abonnements_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.abonnements
    ADD CONSTRAINT abonnements_pkey PRIMARY KEY (id);


--
-- Name: clients clients_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.clients
    ADD CONSTRAINT clients_pkey PRIMARY KEY (id);


--
-- Name: abonnements abonnements_client_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.abonnements
    ADD CONSTRAINT abonnements_client_id_fkey FOREIGN KEY (client_id) REFERENCES public.clients(id);


--
-- Name: SCHEMA public; Type: ACL; Schema: -; Owner: -
--

GRANT ALL ON SCHEMA public TO fred;


--
-- PostgreSQL database dump complete
--


