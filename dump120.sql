--
-- PostgreSQL database dump
--

-- Dumped from database version 12.12 (Debian 12.12-1.pgdg110+1)
-- Dumped by pg_dump version 14.1

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

ALTER TABLE ONLY public.django_admin_log DROP CONSTRAINT django_admin_log_user_id_c564eba6_fk_auth_user_id;
ALTER TABLE ONLY public.django_admin_log DROP CONSTRAINT django_admin_log_content_type_id_c4bce8eb_fk_django_co;
ALTER TABLE ONLY public.auth_user_user_permissions DROP CONSTRAINT auth_user_user_permissions_user_id_a95ead1b_fk_auth_user_id;
ALTER TABLE ONLY public.auth_user_user_permissions DROP CONSTRAINT auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm;
ALTER TABLE ONLY public.auth_user_groups DROP CONSTRAINT auth_user_groups_user_id_6a12ed8b_fk_auth_user_id;
ALTER TABLE ONLY public.auth_user_groups DROP CONSTRAINT auth_user_groups_group_id_97559544_fk_auth_group_id;
ALTER TABLE ONLY public.auth_permission DROP CONSTRAINT auth_permission_content_type_id_2f476e4b_fk_django_co;
ALTER TABLE ONLY public.auth_group_permissions DROP CONSTRAINT auth_group_permissions_group_id_b120cbf9_fk_auth_group_id;
ALTER TABLE ONLY public.auth_group_permissions DROP CONSTRAINT auth_group_permissio_permission_id_84c5c92e_fk_auth_perm;
DROP INDEX public.django_session_session_key_c0390e0f_like;
DROP INDEX public.django_session_expire_date_a5c62663;
DROP INDEX public.django_admin_log_user_id_c564eba6;
DROP INDEX public.django_admin_log_content_type_id_c4bce8eb;
DROP INDEX public.database_urteil_fall_nr_3140ccd2_like;
DROP INDEX public.auth_user_username_6821ab7c_like;
DROP INDEX public.auth_user_user_permissions_user_id_a95ead1b;
DROP INDEX public.auth_user_user_permissions_permission_id_1fbb5f2c;
DROP INDEX public.auth_user_groups_user_id_6a12ed8b;
DROP INDEX public.auth_user_groups_group_id_97559544;
DROP INDEX public.auth_permission_content_type_id_2f476e4b;
DROP INDEX public.auth_group_permissions_permission_id_84c5c92e;
DROP INDEX public.auth_group_permissions_group_id_b120cbf9;
DROP INDEX public.auth_group_name_a6ea08ec_like;
ALTER TABLE ONLY public.django_session DROP CONSTRAINT django_session_pkey;
ALTER TABLE ONLY public.django_migrations DROP CONSTRAINT django_migrations_pkey;
ALTER TABLE ONLY public.django_content_type DROP CONSTRAINT django_content_type_pkey;
ALTER TABLE ONLY public.django_content_type DROP CONSTRAINT django_content_type_app_label_model_76bd3d3b_uniq;
ALTER TABLE ONLY public.django_admin_log DROP CONSTRAINT django_admin_log_pkey;
ALTER TABLE ONLY public.database_urteil DROP CONSTRAINT database_urteil_pkey;
ALTER TABLE ONLY public.database_urteil DROP CONSTRAINT database_urteil_fall_nr_3140ccd2_uniq;
ALTER TABLE ONLY public.database_kimodelpicklefile DROP CONSTRAINT database_kimodelpicklefile_pkey;
ALTER TABLE ONLY public.database_diagrammsvg DROP CONSTRAINT database_diagrammsvg_pkey;
ALTER TABLE ONLY public.auth_user DROP CONSTRAINT auth_user_username_key;
ALTER TABLE ONLY public.auth_user_user_permissions DROP CONSTRAINT auth_user_user_permissions_user_id_permission_id_14a6b632_uniq;
ALTER TABLE ONLY public.auth_user_user_permissions DROP CONSTRAINT auth_user_user_permissions_pkey;
ALTER TABLE ONLY public.auth_user DROP CONSTRAINT auth_user_pkey;
ALTER TABLE ONLY public.auth_user_groups DROP CONSTRAINT auth_user_groups_user_id_group_id_94350c0c_uniq;
ALTER TABLE ONLY public.auth_user_groups DROP CONSTRAINT auth_user_groups_pkey;
ALTER TABLE ONLY public.auth_permission DROP CONSTRAINT auth_permission_pkey;
ALTER TABLE ONLY public.auth_permission DROP CONSTRAINT auth_permission_content_type_id_codename_01ab375a_uniq;
ALTER TABLE ONLY public.auth_group DROP CONSTRAINT auth_group_pkey;
ALTER TABLE ONLY public.auth_group_permissions DROP CONSTRAINT auth_group_permissions_pkey;
ALTER TABLE ONLY public.auth_group_permissions DROP CONSTRAINT auth_group_permissions_group_id_permission_id_0cd325b0_uniq;
ALTER TABLE ONLY public.auth_group DROP CONSTRAINT auth_group_name_key;
ALTER TABLE public.django_migrations ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.django_content_type ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.django_admin_log ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.database_urteil ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.database_kimodelpicklefile ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.database_diagrammsvg ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.auth_user_user_permissions ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.auth_user_groups ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.auth_user ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.auth_permission ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.auth_group_permissions ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.auth_group ALTER COLUMN id DROP DEFAULT;
DROP TABLE public.django_session;
DROP SEQUENCE public.django_migrations_id_seq;
DROP TABLE public.django_migrations;
DROP SEQUENCE public.django_content_type_id_seq;
DROP TABLE public.django_content_type;
DROP SEQUENCE public.django_admin_log_id_seq;
DROP TABLE public.django_admin_log;
DROP SEQUENCE public.database_urteil_id_seq;
DROP TABLE public.database_urteil;
DROP SEQUENCE public.database_kimodelpicklefile_id_seq;
DROP TABLE public.database_kimodelpicklefile;
DROP SEQUENCE public.database_diagrammsvg_id_seq;
DROP TABLE public.database_diagrammsvg;
DROP SEQUENCE public.auth_user_user_permissions_id_seq;
DROP TABLE public.auth_user_user_permissions;
DROP SEQUENCE public.auth_user_id_seq;
DROP SEQUENCE public.auth_user_groups_id_seq;
DROP TABLE public.auth_user_groups;
DROP TABLE public.auth_user;
DROP SEQUENCE public.auth_permission_id_seq;
DROP TABLE public.auth_permission;
DROP SEQUENCE public.auth_group_permissions_id_seq;
DROP TABLE public.auth_group_permissions;
DROP SEQUENCE public.auth_group_id_seq;
DROP TABLE public.auth_group;
SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: auth_group; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.auth_group (
    id integer NOT NULL,
    name character varying(150) NOT NULL
);


--
-- Name: auth_group_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.auth_group_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: auth_group_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.auth_group_id_seq OWNED BY public.auth_group.id;


--
-- Name: auth_group_permissions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.auth_group_permissions (
    id bigint NOT NULL,
    group_id integer NOT NULL,
    permission_id integer NOT NULL
);


--
-- Name: auth_group_permissions_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.auth_group_permissions_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: auth_group_permissions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.auth_group_permissions_id_seq OWNED BY public.auth_group_permissions.id;


--
-- Name: auth_permission; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.auth_permission (
    id integer NOT NULL,
    name character varying(255) NOT NULL,
    content_type_id integer NOT NULL,
    codename character varying(100) NOT NULL
);


--
-- Name: auth_permission_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.auth_permission_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: auth_permission_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.auth_permission_id_seq OWNED BY public.auth_permission.id;


--
-- Name: auth_user; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.auth_user (
    id integer NOT NULL,
    password character varying(128) NOT NULL,
    last_login timestamp with time zone,
    is_superuser boolean NOT NULL,
    username character varying(150) NOT NULL,
    first_name character varying(150) NOT NULL,
    last_name character varying(150) NOT NULL,
    email character varying(254) NOT NULL,
    is_staff boolean NOT NULL,
    is_active boolean NOT NULL,
    date_joined timestamp with time zone NOT NULL
);


--
-- Name: auth_user_groups; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.auth_user_groups (
    id bigint NOT NULL,
    user_id integer NOT NULL,
    group_id integer NOT NULL
);


--
-- Name: auth_user_groups_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.auth_user_groups_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: auth_user_groups_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.auth_user_groups_id_seq OWNED BY public.auth_user_groups.id;


--
-- Name: auth_user_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.auth_user_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: auth_user_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.auth_user_id_seq OWNED BY public.auth_user.id;


--
-- Name: auth_user_user_permissions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.auth_user_user_permissions (
    id bigint NOT NULL,
    user_id integer NOT NULL,
    permission_id integer NOT NULL
);


--
-- Name: auth_user_user_permissions_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.auth_user_user_permissions_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: auth_user_user_permissions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.auth_user_user_permissions_id_seq OWNED BY public.auth_user_user_permissions.id;


--
-- Name: database_diagrammsvg; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.database_diagrammsvg (
    id bigint NOT NULL,
    name character varying(50) NOT NULL,
    file character varying(100) NOT NULL,
    last_updated timestamp with time zone NOT NULL,
    lesehinweis character varying(1000)
);


--
-- Name: database_diagrammsvg_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.database_diagrammsvg_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: database_diagrammsvg_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.database_diagrammsvg_id_seq OWNED BY public.database_diagrammsvg.id;


--
-- Name: database_kimodelpicklefile; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.database_kimodelpicklefile (
    id bigint NOT NULL,
    name character varying(30) NOT NULL,
    file character varying(100) NOT NULL,
    last_updated timestamp with time zone NOT NULL,
    prognoseleistung_dict jsonb NOT NULL,
    encoder character varying(100) NOT NULL,
    ft_importance_list jsonb,
    ft_importance_list_merged jsonb
);


--
-- Name: database_kimodelpicklefile_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.database_kimodelpicklefile_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: database_kimodelpicklefile_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.database_kimodelpicklefile_id_seq OWNED BY public.database_kimodelpicklefile.id;


--
-- Name: database_urteil; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.database_urteil (
    id bigint NOT NULL,
    fall_nr character varying(15) NOT NULL,
    verfahrensart character varying(2) NOT NULL,
    geschlecht character varying(2) NOT NULL,
    mehrfach boolean NOT NULL,
    gewerbsmaessig boolean NOT NULL,
    deliktssumme integer NOT NULL,
    bandenmaessig boolean NOT NULL,
    freiheitsstrafe_in_monaten integer NOT NULL,
    nebenverurteilungsscore integer NOT NULL,
    vorbestraft boolean NOT NULL,
    vorbestraft_einschlaegig boolean NOT NULL,
    hauptdelikt character varying(30) NOT NULL,
    vollzug character varying(20) NOT NULL,
    url_link character varying(200) NOT NULL,
    gericht character varying(30) NOT NULL,
    nationalitaet character varying(2) NOT NULL,
    urteilsdatum date
);


--
-- Name: database_urteil_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.database_urteil_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: database_urteil_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.database_urteil_id_seq OWNED BY public.database_urteil.id;


--
-- Name: django_admin_log; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.django_admin_log (
    id integer NOT NULL,
    action_time timestamp with time zone NOT NULL,
    object_id text,
    object_repr character varying(200) NOT NULL,
    action_flag smallint NOT NULL,
    change_message text NOT NULL,
    content_type_id integer,
    user_id integer NOT NULL,
    CONSTRAINT django_admin_log_action_flag_check CHECK ((action_flag >= 0))
);


--
-- Name: django_admin_log_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.django_admin_log_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: django_admin_log_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.django_admin_log_id_seq OWNED BY public.django_admin_log.id;


--
-- Name: django_content_type; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.django_content_type (
    id integer NOT NULL,
    app_label character varying(100) NOT NULL,
    model character varying(100) NOT NULL
);


--
-- Name: django_content_type_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.django_content_type_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: django_content_type_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.django_content_type_id_seq OWNED BY public.django_content_type.id;


--
-- Name: django_migrations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.django_migrations (
    id bigint NOT NULL,
    app character varying(255) NOT NULL,
    name character varying(255) NOT NULL,
    applied timestamp with time zone NOT NULL
);


--
-- Name: django_migrations_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.django_migrations_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: django_migrations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.django_migrations_id_seq OWNED BY public.django_migrations.id;


--
-- Name: django_session; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.django_session (
    session_key character varying(40) NOT NULL,
    session_data text NOT NULL,
    expire_date timestamp with time zone NOT NULL
);


--
-- Name: auth_group id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auth_group ALTER COLUMN id SET DEFAULT nextval('public.auth_group_id_seq'::regclass);


--
-- Name: auth_group_permissions id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auth_group_permissions ALTER COLUMN id SET DEFAULT nextval('public.auth_group_permissions_id_seq'::regclass);


--
-- Name: auth_permission id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auth_permission ALTER COLUMN id SET DEFAULT nextval('public.auth_permission_id_seq'::regclass);


--
-- Name: auth_user id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auth_user ALTER COLUMN id SET DEFAULT nextval('public.auth_user_id_seq'::regclass);


--
-- Name: auth_user_groups id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auth_user_groups ALTER COLUMN id SET DEFAULT nextval('public.auth_user_groups_id_seq'::regclass);


--
-- Name: auth_user_user_permissions id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auth_user_user_permissions ALTER COLUMN id SET DEFAULT nextval('public.auth_user_user_permissions_id_seq'::regclass);


--
-- Name: database_diagrammsvg id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.database_diagrammsvg ALTER COLUMN id SET DEFAULT nextval('public.database_diagrammsvg_id_seq'::regclass);


--
-- Name: database_kimodelpicklefile id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.database_kimodelpicklefile ALTER COLUMN id SET DEFAULT nextval('public.database_kimodelpicklefile_id_seq'::regclass);


--
-- Name: database_urteil id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.database_urteil ALTER COLUMN id SET DEFAULT nextval('public.database_urteil_id_seq'::regclass);


--
-- Name: django_admin_log id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.django_admin_log ALTER COLUMN id SET DEFAULT nextval('public.django_admin_log_id_seq'::regclass);


--
-- Name: django_content_type id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.django_content_type ALTER COLUMN id SET DEFAULT nextval('public.django_content_type_id_seq'::regclass);


--
-- Name: django_migrations id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.django_migrations ALTER COLUMN id SET DEFAULT nextval('public.django_migrations_id_seq'::regclass);


--
-- Data for Name: auth_group; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.auth_group (id, name) FROM stdin;
\.


--
-- Data for Name: auth_group_permissions; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.auth_group_permissions (id, group_id, permission_id) FROM stdin;
\.


--
-- Data for Name: auth_permission; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.auth_permission (id, name, content_type_id, codename) FROM stdin;
1	Can add log entry	1	add_logentry
2	Can change log entry	1	change_logentry
3	Can delete log entry	1	delete_logentry
4	Can view log entry	1	view_logentry
5	Can add permission	2	add_permission
6	Can change permission	2	change_permission
7	Can delete permission	2	delete_permission
8	Can view permission	2	view_permission
9	Can add group	3	add_group
10	Can change group	3	change_group
11	Can delete group	3	delete_group
12	Can view group	3	view_group
13	Can add user	4	add_user
14	Can change user	4	change_user
15	Can delete user	4	delete_user
16	Can view user	4	view_user
17	Can add content type	5	add_contenttype
18	Can change content type	5	change_contenttype
19	Can delete content type	5	delete_contenttype
20	Can view content type	5	view_contenttype
21	Can add session	6	add_session
22	Can change session	6	change_session
23	Can delete session	6	delete_session
24	Can view session	6	view_session
25	Can add urteil	7	add_urteil
26	Can change urteil	7	change_urteil
27	Can delete urteil	7	delete_urteil
28	Can view urteil	7	view_urteil
29	Can add ki model pickle file	8	add_kimodelpicklefile
30	Can change ki model pickle file	8	change_kimodelpicklefile
31	Can delete ki model pickle file	8	delete_kimodelpicklefile
32	Can view ki model pickle file	8	view_kimodelpicklefile
33	Can add diagramm svg	9	add_diagrammsvg
34	Can change diagramm svg	9	change_diagrammsvg
35	Can delete diagramm svg	9	delete_diagrammsvg
36	Can view diagramm svg	9	view_diagrammsvg
\.


--
-- Data for Name: auth_user; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.auth_user (id, password, last_login, is_superuser, username, first_name, last_name, email, is_staff, is_active, date_joined) FROM stdin;
1	pbkdf2_sha256$260000$QtaN26Y6vVeGhv7NoEBF1R$cUQxZPk13c42uI47/cuE8JJF0D+NnEv71Rec4+wpnPk=	2023-04-15 07:18:17.64692+00	t	jonasachermann			jonasachermann@mac.com	t	t	2021-11-07 22:02:20.593968+00
\.


--
-- Data for Name: auth_user_groups; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.auth_user_groups (id, user_id, group_id) FROM stdin;
\.


--
-- Data for Name: auth_user_user_permissions; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.auth_user_user_permissions (id, user_id, permission_id) FROM stdin;
\.


--
-- Data for Name: database_diagrammsvg; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.database_diagrammsvg (id, name, file, last_updated, lesehinweis) FROM stdin;
1	Beispielurteile	diagramme/beispielbild.png	2023-03-01 11:26:38.650723+00	\N
3	vollzug_scatterplot_1000000	diagramme/vollzug_scatterplot_1000000.svg	2023-04-18 13:47:12.115103+00	\N
4	vollzug_scatterplot_200000	diagramme/vollzug_scatterplot_200000.svg	2023-04-18 13:47:12.316854+00	\N
6	hauptdelikt_scatterplot_1000000	diagramme/hauptdelikt_scatterplot_1000000.svg	2023-04-18 13:47:12.563531+00	\N
7	hauptdelikt_scatterplot_200000	diagramme/hauptdelikt_scatterplot_200000.svg	2023-04-18 13:47:12.816343+00	\N
5	nationalitaet_scatterplot_1000000	diagramme/nationalitaet_scatterplot_1000000.svg	2023-03-10 15:56:36.174991+00	\N
2	nationalitaet_scatterplot_200000	diagramme/nationalitaet_scatterplot_200000.svg	2023-03-10 15:56:36.396749+00	\N
8	introspection_plot	diagramme/introspection_plot.svg	2023-04-18 13:46:18.965977+00	<p>Der Liniengraph bildet die Prognose bei unterschiedlichen Deliktssummen ab, wenn die übrigen Sachverhaltsmerkmale – ceteribus paribus – wie folgt bestehen bleiben: </p><ul><li>Geschlecht: Männlich, </li><li>mehrfache Tatbegehung: nicht zutreffend, </li><li>gewerbsmässige Tatbegehung: nicht zutreffend, </li><li>bandenmässige Tatbegehung: nicht zutreffend, </li><li>Nebenverurteilungsscore: 0, </li><li>Vorbestraft: nicht zutreffend, </li><li>Einschlägig vorbestraft: nicht zutreffend </li></ul>
\.


--
-- Data for Name: database_kimodelpicklefile; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.database_kimodelpicklefile (id, name, file, last_updated, prognoseleistung_dict, encoder, ft_importance_list, ft_importance_list_merged) FROM stdin;
9	lr_regr_all	pickles/linear_regression_regressor_all_fts.pkl	2023-04-18 13:45:57.594854+00	{"standardabweichung": 7.96, "beste_prognoseleistung": 0.22, "durchschnittlicher_fehler": 10.35, "standardabweichung_string": "67.5% aller Prognosen weisen einen Fehler zwischen 2.4 und 18.31 Monaten auf", "beste_prognoseleistung_index": 79, "schlechteste_prognoseleistung": 37.16, "schlechteste_prognoseleistung_index": 42}		\N	\N
11	rf_clf_val	pickles/random_forest_classifier_val_fts.pkl	2023-04-18 13:45:54.278051+00	{"content": "empty"}		[[30.578433643419125, "deliktssumme"], [14.930684233382777, "nebenverurteilungsscore"], [7.92194090268573, "vorbestraft_True"], [7.2508786149994915, "vorbestraft_einschlaegig_True"], [6.271163308274214, "vorbestraft_False"], [6.141221412583245, "vorbestraft_einschlaegig_False"], [4.33501469264247, "gewerbsmaessig_True"], [3.650704237337818, "gewerbsmaessig_False"], [3.342556323830015, "hauptdelikt_Betrug"], [3.231127465413401, "mehrfach_False"], [3.0571086855329987, "mehrfach_True"], [2.9527714208121445, "hauptdelikt_Veruntreuung"], [2.497926085383573, "hauptdelikt_Diebstahl"], [1.861670242022543, "hauptdelikt_ung. Geschäftsbesorgung"], [0.9927557914967325, "hauptdelikt_betr. Missbrauch DVA"], [0.4701047902584199, "hauptdelikt_Sachbeschädigung"], [0.2575215823909886, "bandenmaessig_True"], [0.2564165675343149, "bandenmaessig_False"]]	[[30.578433643419125, "deliktssumme"], [14.930684233382777, "nebenverurteilungsscore"], [14.193104210959945, "vorbestraft"], [13.392100027582737, "einschlaegig_vorbestraft"], [12.117784653803428, "hauptdelikt"], [7.985718929980287, "gewerbsmaessig"], [6.2882361509464, "mehrfach"], [0.5139381499253035, "bandenmaessig"], [0, "geschlecht"], [0, "nationalitaet"], [0, "gericht"]]
10	rf_regr_val	pickles/random_forest_regressor_val_fts.pkl	2023-04-18 13:45:53.869171+00	{"standardabweichung": 6.46, "beste_prognoseleistung": 0.01, "durchschnittlicher_fehler": 7.14, "standardabweichung_string": "75.0% aller Prognosen weisen einen Fehler zwischen 0.68 und 13.6 Monaten auf", "beste_prognoseleistung_index": 97, "beste_prognoseleistung_urteil": "SB210319", "schlechteste_prognoseleistung": 32.33, "schlechteste_prognoseleistung_index": 30, "schlechteste_prognoseleistung_urteil": "SB160371"}	encoders/one_hot_encoder_fuer_rf_regr_val.pkl	[[48.53479883756823, "deliktssumme"], [17.309056158905328, "nebenverurteilungsscore"], [11.583400487151692, "gewerbsmaessig_True"], [9.545363544490263, "gewerbsmaessig_False"], [4.733879464201567, "vorbestraft_einschlaegig_False"], [2.986912378693354, "vorbestraft_False"], [1.8290647300718912, "hauptdelikt_Betrug"], [1.6099183766065208, "vorbestraft_True"], [0.6146983270465428, "mehrfach_False"], [0.6044065698023058, "hauptdelikt_Diebstahl"], [0.47987731128644573, "mehrfach_True"], [0.16862381417585676, "vorbestraft_einschlaegig_True"], [0.0, "hauptdelikt_Sachbeschädigung"], [0.0, "hauptdelikt_Veruntreuung"], [0.0, "hauptdelikt_betr. Missbrauch DVA"], [0.0, "hauptdelikt_ung. Geschäftsbesorgung"], [0.0, "bandenmaessig_False"], [0.0, "bandenmaessig_True"]]	[[48.53479883756823, "deliktssumme"], [21.128764031641957, "gewerbsmaessig"], [17.309056158905328, "nebenverurteilungsscore"], [4.902503278377424, "einschlaegig_vorbestraft"], [4.596830755299875, "vorbestraft"], [2.433471299874197, "hauptdelikt"], [1.0945756383329885, "mehrfach"], [0, "geschlecht"], [0, "nationalitaet"], [0, "gericht"], [0.0, "bandenmaessig"]]
8	rf_regr_all	pickles/random_forest_regressor_all_fts.pkl	2023-04-18 13:45:56.987928+00	{"standardabweichung": 6.42, "beste_prognoseleistung": 0.04, "durchschnittlicher_fehler": 7.15, "standardabweichung_string": "80.0% aller Prognosen weisen einen Fehler zwischen 0.73 und 13.57 Monaten auf", "beste_prognoseleistung_index": 48, "schlechteste_prognoseleistung": 33.01, "schlechteste_prognoseleistung_index": 30}		[[46.405716387439824, "deliktssumme"], [16.626932309436672, "nebenverurteilungsscore"], [11.945316630374489, "gewerbsmaessig_True"], [8.76983243357462, "gewerbsmaessig_False"], [2.8575952781049, "vorbestraft_False"], [2.756855301088601, "vorbestraft_einschlaegig_False"], [2.0030223819395245, "vorbestraft_einschlaegig_True"], [1.91209447112114, "urteilsjahr"], [1.7190058773968113, "gericht_Bezirksgericht Zürich"], [1.4450486698603164, "hauptdelikt_Betrug"], [1.4441414747934243, "vorbestraft_True"], [0.6082458414681838, "mehrfach_False"], [0.4406897849090664, "hauptdelikt_Diebstahl"], [0.4219823348220221, "mehrfach_True"], [0.34656852063036636, "nationalitaet_Ausländerin/Ausländer"], [0.15827382081120447, "nationalitaet_unbekannt"], [0.10062501783044545, "geschlecht_männlich"], [0.0380534643983949, "geschlecht_weiblich"], [0.0, "hauptdelikt_Sachbeschädigung"], [0.0, "hauptdelikt_Veruntreuung"], [0.0, "hauptdelikt_betr. Missbrauch DVA"], [0.0, "hauptdelikt_ung. Geschäftsbesorgung"], [0.0, "nationalitaet_Schweizerin/Schweizer"], [0.0, "gericht_Bezirksgericht Bülach"], [0.0, "gericht_Bezirksgericht Dielsdorf"], [0.0, "gericht_Bezirksgericht Dietikon"], [0.0, "gericht_Bezirksgericht Hinwil"], [0.0, "gericht_Bezirksgericht Horgen"], [0.0, "gericht_Bezirksgericht Meilen"], [0.0, "gericht_Bezirksgericht Pfäffikon"], [0.0, "gericht_Bezirksgericht Päffikon"], [0.0, "gericht_Bezirksgericht Uster"], [0.0, "gericht_Bezirksgericht Winterthur"]]	[[46.405716387439824, "deliktssumme"], [20.71514906394911, "gewerbsmaessig"], [16.626932309436672, "nebenverurteilungsscore"], [4.759877683028126, "einschlaegig_vorbestraft"], [4.301736752898324, "vorbestraft"], [1.91209447112114, "urteilsjahr"], [1.885738454769383, "hauptdelikt"], [1.7190058773968113, "gericht"], [1.030228176290206, "mehrfach"], [0.5048423414415708, "nationalitaet"], [0.13867848222884036, "geschlecht"], [0, "bandenmaessig"]]
\.


--
-- Data for Name: database_urteil; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.database_urteil (id, fall_nr, verfahrensart, geschlecht, mehrfach, gewerbsmaessig, deliktssumme, bandenmaessig, freiheitsstrafe_in_monaten, nebenverurteilungsscore, vorbestraft, vorbestraft_einschlaegig, hauptdelikt, vollzug, url_link, gericht, nationalitaet, urteilsdatum) FROM stdin;
96	SB210265	0	1	f	f	290000	f	30	8	f	f	Veruntreuung	1	https://www.gerichte-zh.ch/fileadmin/user_upload/entscheide/oeffentlich/SB210265-O1.pdf	Bezirksgericht Horgen	2	2020-08-11
104	SB210285	0	0	f	t	44000	f	7	0	f	f	Betrug	0	https://www.gerichte-zh.ch/fileadmin/user_upload/entscheide/oeffentlich/SB210285-O1.pdf	Bezirksgericht Zürich	1	2021-03-29
98	SB210045	0	0	f	t	100001	f	24	0	t	f	Betrug	0	https://www.gerichte-zh.ch/fileadmin/user_upload/entscheide/oeffentlich/SB210045-O1.pdf	Bezirksgericht Dietikon	1	2020-11-16
11	SB190520	0	0	f	t	802953	f	30	3	f	f	Betrug	1	https://www.gerichte-zh.ch/fileadmin/user_upload/entscheide/oeffentlich/SB190520-O1.pdf	Bezirksgericht Horgen	2	2019-05-15
5	SB180363	0	1	t	f	215338	f	18	2	f	f	Betrug	0	https://entscheidsuche.ch/docs/ZH_Obergericht/ZH_OG_002_SB180363_2019-06-25.pdf	Bezirksgericht Winterthur	1	2018-05-16
52	SB190523	0	0	t	f	487000	f	27	8	f	f	Veruntreuung	1	https://www.gerichte-zh.ch/fileadmin/user_upload/entscheide/oeffentlich/SB190523-O1.pdf	Bezirksgericht Zürich	2	2021-04-22
47	SB150207	0	0	t	f	362000	f	14	2	f	f	ung. Geschäftsbesorgung	0	https://www.gerichte-zh.ch/fileadmin/user_upload/entscheide/oeffentlich/SB150207-O1.pdf	Bezirksgericht Zürich	2	2015-04-01
9	SB210165	0	0	f	t	450600	f	33	0	t	f	Betrug	1	https://www.gerichte-zh.ch/fileadmin/user_upload/entscheide/oeffentlich/SB210165-O1.pdf	Bezirksgericht Winterthur	2	2020-11-12
45	SB180182	0	0	f	f	3000000	f	22	0	t	t	ung. Geschäftsbesorgung	0	https://www.gerichte-zh.ch/fileadmin/user_upload/entscheide/oeffentlich/SB180182-O1.pdf	Bezirksgericht Zürich	2	2018-02-28
2	SB200202	0	0	f	t	19363	f	30	7	t	t	Betrug	2	https://www.gerichte-zh.ch/fileadmin/user_upload/entscheide/oeffentlich/SB200202-O1.pdf	Bezirksgericht Zürich	2	2020-01-28
105	SB210508	0	0	f	f	5000	f	6	0	t	t	Betrug	0	https://www.gerichte-zh.ch/fileadmin/user_upload/entscheide/oeffentlich/SB210508-O1.pdf	Bezirksgericht Dietikon	1	2021-07-07
53	SB180264	0	0	t	f	169062	f	27	7	t	t	ung. Geschäftsbesorgung	2	https://www.gerichte-zh.ch/fileadmin/user_upload/entscheide/oeffentlich/SB180264-O1.pdf	Bezirksgericht Zürich	2	2018-03-21
57	SB190110	0	1	f	f	133090	f	20	0	f	f	Veruntreuung	0	https://www.gerichte-zh.ch/fileadmin/user_upload/entscheide/oeffentlich/SB190110-O1.pdf	Bezirksgericht Dietikon	2	2018-09-12
55	SB200078	0	0	f	f	85000	f	8	0	t	t	Betrug	2	https://www.gerichte-zh.ch/fileadmin/user_upload/entscheide/oeffentlich/SB200078-O1.pdf	Bezirksgericht Pfäffikon	1	2019-07-16
61	SB190476	0	0	f	f	1232296	f	54	14	t	t	ung. Geschäftsbesorgung	2	https://www.gerichte-zh.ch/fileadmin/user_upload/entscheide/oeffentlich/SB190476-O1.pdf	Bezirksgericht Zürich	2	2019-06-26
102	SB210193	0	0	f	f	280134	f	10	3	f	f	Betrug	0	https://www.gerichte-zh.ch/fileadmin/user_upload/entscheide/oeffentlich/SB210193-O1.pdf	Bezirksgericht Horgen	0	2020-11-30
109	SB210242	0	1	t	f	300	f	14	8	t	t	Diebstahl	0	https://www.gerichte-zh.ch/fileadmin/user_upload/entscheide/oeffentlich/SB210242-O1.pdf	Bezirksgericht Zürich	1	2021-01-28
54	SB200291	0	0	f	t	116000	f	30	3	t	t	Betrug	2	https://www.gerichte-zh.ch/fileadmin/user_upload/entscheide/oeffentlich/SB200291-O1.pdf	Bezirksgericht Zürich	2	2020-05-06
46	SB160422	0	0	f	f	139000	f	16	0	t	f	ung. Geschäftsbesorgung	0	https://www.gerichte-zh.ch/fileadmin/user_upload/entscheide/oeffentlich/SB160422-O1.pdf	Bezirksgericht Bülach	2	2014-09-18
60	SB180066	0	0	t	f	15000	f	7	3	t	t	Veruntreuung	2	https://www.gerichte-zh.ch/fileadmin/user_upload/entscheide/oeffentlich/SB180066-O1.pdf	Bezirksgericht Zürich	2	2017-10-30
106	SB210241	0	0	f	f	170000	f	28	0	f	f	Betrug	1	https://www.gerichte-zh.ch/fileadmin/user_upload/entscheide/oeffentlich/SB210241-O1.pdf	Bezirksgericht Dielsdorf	1	2020-10-02
10	SB180491	0	0	f	t	10000	f	12	2	t	t	Betrug	2	https://www.gerichte-zh.ch/fileadmin/user_upload/entscheide/oeffentlich/SB180491-O1.pdf	Bezirksgericht Meilen	1	2018-08-23
51	SB200466	0	0	f	f	70000	f	10	2	t	f	ung. Geschäftsbesorgung	2	https://www.gerichte-zh.ch/fileadmin/user_upload/entscheide/oeffentlich/SB200466-O2.pdf	Bezirksgericht Dietikon	2	2020-09-29
100	SB210163	0	0	t	f	239729	f	18	0	f	f	ung. Geschäftsbesorgung	0	https://www.gerichte-zh.ch/fileadmin/user_upload/entscheide/oeffentlich/SB210163-O1.pdf	Bezirksgericht Zürich	2	2020-10-15
97	SB150028	0	0	f	f	806146	f	24	4	f	f	Betrug	0	https://www.gerichte-zh.ch/fileadmin/user_upload/entscheide/oeffentlich/SB150028-O1.pdf	Bezirksgericht Zürich	2	2014-12-16
116	SB210503	0	0	t	f	50000	f	16	8	t	t	betr. Missbrauch DVA	2	https://www.gerichte-zh.ch/fileadmin/user_upload/entscheide/oeffentlich/SB210503-O1.pdf	Bezirksgericht Meilen	1	2021-07-08
4	SB170236	0	0	f	t	346693	f	54	5	t	t	betr. Missbrauch DVA	2	https://www.gerichte-zh.ch/fileadmin/user_upload/entscheide/oeffentlich/SB170236-O1.pdf	Bezirksgericht Zürich	2	2017-03-02
6	SB200427	0	0	f	f	2400	f	5	3	t	t	Betrug	2	https://www.gerichte-zh.ch/fileadmin/user_upload/entscheide/oeffentlich/SB200427-O1.pdf	Bezirksgericht Uster	1	2020-06-26
101	SB190567	0	0	f	t	474000	f	45	7	t	t	Betrug	2	https://www.gerichte-zh.ch/fileadmin/user_upload/entscheide/oeffentlich/SB190567-O1.pdf	Bezirksgericht Zürich	2	2019-08-28
58	SB180545	0	0	t	f	562375	f	18	4	f	f	Veruntreuung	0	https://www.gerichte-zh.ch/fileadmin/user_upload/entscheide/oeffentlich/SB180545-O1.pdf	Bezirksgericht Dielsdorf	2	2018-02-23
3	SB170444	0	1	f	f	40000	f	36	2	t	t	Betrug	2	https://www.gerichte-zh.ch/fileadmin/user_upload/entscheide/oeffentlich/SB170444-O1.pdf	Bezirksgericht Bülach	1	2017-07-18
8	SB190020	0	0	t	f	100001	f	14	0	f	f	betr. Missbrauch DVA	0	https://www.gerichte-zh.ch/fileadmin/user_upload/entscheide/oeffentlich/SB190020-O1.pdf	Bezirksgericht Zürich	2	2018-11-08
1	SB200112	0	1	f	f	59311	f	8	0	f	f	Betrug	0	https://www.gerichte-zh.ch/fileadmin/user_upload/entscheide/oeffentlich/SB200112-O1.pdf	Bezirksgericht Zürich	2	2019-12-10
99	SB210497	0	0	f	f	80000	f	12	2	t	f	Betrug	0	https://www.gerichte-zh.ch/fileadmin/user_upload/entscheide/oeffentlich/SB210497-O1.pdf	Bezirksgericht Dietikon	2	2021-04-27
114	SB130128	0	0	f	f	111200	f	12	3	f	f	betr. Missbrauch DVA	0	https://www.gerichte-zh.ch/fileadmin/user_upload/entscheide/oeffentlich/SB130128-O1.pdf	Bezirksgericht Hinwil	2	2012-12-04
56	SB190389	0	0	t	f	847955	f	39	0	t	f	Veruntreuung	2	https://www.gerichte-zh.ch/fileadmin/user_upload/entscheide/oeffentlich/SB190389-O1.pdf	Bezirksgericht Winterthur	2	2019-06-12
12	SB190490	0	0	t	f	2360	f	9	5	t	t	betr. Missbrauch DVA	2	https://www.gerichte-zh.ch/fileadmin/user_upload/entscheide/oeffentlich/SB190490-O1.pdf	Bezirksgericht Horgen	2	2019-07-11
62	SB200012	0	0	t	f	9012	f	6	0	f	f	ung. Geschäftsbesorgung	0	https://www.gerichte-zh.ch/fileadmin/user_upload/entscheide/oeffentlich/SB200012-O1.pdf	Bezirksgericht Winterthur	0	2019-10-03
50	SB190267	0	0	t	f	40000	f	5	0	f	f	Veruntreuung	0	https://www.gerichte-zh.ch/fileadmin/user_upload/entscheide/oeffentlich/SB190267-O1.pdf	Bezirksgericht Bülach	1	2019-01-18
123	SB200480	0	0	f	t	184000	f	48	0	t	t	Diebstahl	2	https://www.gerichte-zh.ch/fileadmin/user_upload/entscheide/oeffentlich/SB200480-O1.pdf	Bezirksgericht Zürich	1	2020-09-10
59	SB170415	0	1	t	f	10000000	f	30	6	f	f	ung. Geschäftsbesorgung	1	https://www.gerichte-zh.ch/fileadmin/user_upload/entscheide/oeffentlich/SB170415-O1.pdf	Bezirksgericht Zürich	1	2017-08-23
111	SB210362	0	0	t	f	301	f	8	1	t	t	Sachbeschädigung	0	https://www.gerichte-zh.ch/fileadmin/user_upload/entscheide/oeffentlich/SB210362-O1.pdf	Bezirksgericht Zürich	2	2021-05-27
113	SB140409	0	0	f	t	299999	f	24	0	f	f	betr. Missbrauch DVA	0	https://www.gerichte-zh.ch/fileadmin/user_upload/entscheide/oeffentlich/SB140409-O1.pdf	Bezirksgericht Uster	2	2014-05-15
115	SB130034	0	0	f	t	1054694	f	36	8	f	f	betr. Missbrauch DVA	1	https://www.gerichte-zh.ch/fileadmin/user_upload/entscheide/oeffentlich/SB130034-O1.pdf	Bezirksgericht Dietikon	2	2012-11-28
117	SB160162	0	0	f	t	8366	f	8	1	t	t	Betrug	2	https://www.gerichte-zh.ch/fileadmin/user_upload/entscheide/oeffentlich/SB160162-O1.pdf	Bezirksgericht Zürich	2	2016-01-18
121	SB210246	0	1	f	t	23403	f	30	4	f	f	Diebstahl	1	https://www.gerichte-zh.ch/fileadmin/user_upload/entscheide/oeffentlich/SB210246-O1.pdf	Bezirksgericht Meilen	1	2020-11-26
119	SB190113	0	0	f	t	160000	f	48	4	t	t	Diebstahl	2	https://www.gerichte-zh.ch/fileadmin/user_upload/entscheide/oeffentlich/SB190113-O1.pdf	Bezirksgericht Winterthur	1	2018-10-25
122	SB210031	0	1	f	t	17900	f	27	2	t	t	Diebstahl	2	https://www.gerichte-zh.ch/fileadmin/user_upload/entscheide/oeffentlich/SB210031-O1.pdf	Bezirksgericht Zürich	1	2020-09-10
118	SB200244	0	0	f	t	500001	f	66	4	t	t	Diebstahl	2	https://www.gerichte-zh.ch/fileadmin/user_upload/entscheide/oeffentlich/SB200244-O1.pdf	Bezirksgericht Zürich	1	2020-02-10
110	SB210654	0	0	f	t	19189	f	30	4	t	t	Diebstahl	2	https://www.gerichte-zh.ch/fileadmin/user_upload/entscheide/oeffentlich/SB210654-O1.pdf	Bezirksgericht Dielsdorf	0	2021-08-30
112	SB210428	0	0	f	t	26758	t	54	9	t	t	Diebstahl	2	https://www.gerichte-zh.ch/fileadmin/user_upload/entscheide/oeffentlich/SB210428-O1.pdf	Bezirksgericht Zürich	1	2021-06-10
124	SB200411	0	0	f	t	20000	f	37	7	t	t	Diebstahl	2	https://www.gerichte-zh.ch/fileadmin/user_upload/entscheide/oeffentlich/SB200411-O1.pdf	Bezirksgericht Zürich	1	2020-06-11
125	SB200129	0	0	f	t	26000	f	40	5	t	t	Diebstahl	2	https://www.gerichte-zh.ch/fileadmin/user_upload/entscheide/oeffentlich/SB200129-O1.pdf	Bezirksgericht Winterthur	1	2019-11-27
126	SB190561	0	1	f	t	80000	f	30	3	f	f	Diebstahl	1	https://www.gerichte-zh.ch/fileadmin/user_upload/entscheide/oeffentlich/SB190561-O2.pdf	Bezirksgericht Winterthur	1	2019-08-21
127	SB190160	0	0	t	t	17800	t	8	2	t	t	Diebstahl	0	https://www.gerichte-zh.ch/fileadmin/user_upload/entscheide/oeffentlich/SB190160-O1.pdf	Bezirksgericht Bülach	1	2018-11-06
49	SB200453	0	0	f	f	2500	f	10	6	t	t	Veruntreuung	2	https://www.gerichte-zh.ch/fileadmin/user_upload/entscheide/oeffentlich/SB200453-O1.pdf	Bezirksgericht Dietikon	2	2020-06-03
103	SB210054	0	0	f	t	31918	f	9	2	t	t	betr. Missbrauch DVA	2	https://www.gerichte-zh.ch/fileadmin/user_upload/entscheide/oeffentlich/SB210054-O1.pdf	Bezirksgericht Zürich	1	2020-10-13
63	SB150048	0	0	f	t	435459	f	48	3	t	t	betr. Missbrauch DVA	2	https://www.gerichte-zh.ch/fileadmin/user_upload/entscheide/oeffentlich/SB150048-O1.pdf	Bezirksgericht Zürich	2	2014-12-02
120	SB180343	0	0	f	t	34000	f	30	2	t	t	Betrug	2	https://www.gerichte-zh.ch/fileadmin/user_upload/entscheide/oeffentlich/SB180343-O1.pdf	Bezirksgericht Zürich	2	2018-05-23
129	SB210341	0	1	f	t	1300000	f	32	3	f	f	Betrug	1	https://www.gerichte-zh.ch/fileadmin/user_upload/entscheide/oeffentlich/SB210341-O1.pdf	Bezirksgericht Zürich	2	2021-04-12
130	SB210028	0	0	f	f	61500	f	7	4	t	t	Veruntreuung	0	https://www.gerichte-zh.ch/fileadmin/user_upload/entscheide/oeffentlich/SB210028-O1.pdf	Bezirksgericht Zürich	2	2020-10-02
131	SB180036	0	0	f	f	299	f	6	1	t	t	Diebstahl	2	https://www.gerichte-zh.ch/fileadmin/user_upload/entscheide/oeffentlich/SB180036-O1.pdf	Bezirksgericht Uster	1	2017-08-08
132	SB210127	0	0	t	f	1845	f	9	1	t	t	Diebstahl	0	https://www.gerichte-zh.ch/fileadmin/user_upload/entscheide/oeffentlich/SB210127-O1.pdf	Bezirksgericht Zürich	1	2020-11-19
133	SB200013	0	1	t	f	1500	f	8	2	f	f	Diebstahl	0	https://www.gerichte-zh.ch/fileadmin/user_upload/entscheide/oeffentlich/SB200013-O1.pdf	Bezirksgericht Winterthur	1	2019-09-13
134	SB210233	0	0	t	f	22600	f	31	9	t	t	Diebstahl	2	https://www.gerichte-zh.ch/fileadmin/user_upload/entscheide/oeffentlich/SB210233-O1.pdf	Bezirksgericht Bülach	1	2020-12-17
135	SB180109	0	0	f	t	3724	f	16	3	t	t	betr. Missbrauch DVA	0	https://www.gerichte-zh.ch/fileadmin/user_upload/entscheide/oeffentlich/SB180109-O1.pdf	Bezirksgericht Zürich	1	2017-12-07
136	SB190217	0	0	t	f	2115	f	12	2	t	t	Diebstahl	2	https://www.gerichte-zh.ch/fileadmin/user_upload/entscheide/oeffentlich/SB190217-O1.pdf	Bezirksgericht Winterthur	1	2019-02-21
137	SB180508	0	0	f	t	118200	f	20	0	t	f	Betrug	2	https://www.gerichte-zh.ch/fileadmin/user_upload/entscheide/oeffentlich/SB180508-O1.pdf	Bezirksgericht Bülach	1	2018-10-03
138	SB200048	0	0	f	t	815000	f	48	3	t	f	Betrug	2	https://www.gerichte-zh.ch/fileadmin/user_upload/entscheide/oeffentlich/SB200048-O1.pdf	Bezirksgericht Zürich	1	2019-11-01
139	SB200069	0	0	t	t	212967	f	24	0	t	f	Betrug	0	https://www.gerichte-zh.ch/fileadmin/user_upload/entscheide/oeffentlich/SB200069-O1.pdf	Bezirksgericht Zürich	1	2019-11-06
140	SB180525	0	0	f	t	135600	f	30	1	t	t	Betrug	2	https://www.gerichte-zh.ch/fileadmin/user_upload/entscheide/oeffentlich/SB180525-O1.pdf	Bezirksgericht Winterthur	1	2018-07-12
142	SB190367	0	0	f	t	723432	f	34	3	t	f	Betrug	1	https://entscheidsuche.ch/docs/ZH_Obergericht/ZH_OG_002_SB190367_2020-09-25.pdf	Bezirksgericht Zürich	1	2019-06-24
143	SB180517	0	0	f	t	17330	t	32	4	t	t	Diebstahl	2	https://www.gerichte-zh.ch/fileadmin/user_upload/entscheide/oeffentlich/SB180517-O1.pdf	Bezirksgericht Dielsdorf	1	2018-03-23
144	SB200250	0	0	f	t	150000	t	66	6	t	t	Betrug	2	https://entscheidsuche.ch/docs/ZH_Obergericht/ZH_OG_002_SB200250_2021-02-15.pdf	Bezirksgericht Winterthur	1	2020-02-04
141	SB170498	0	0	f	t	400000	f	29	0	t	f	Betrug	2	https://www.gerichte-zh.ch/fileadmin/user_upload/entscheide/oeffentlich/SB170498-O1.pdf	Bezirksgericht Dietikon	2	2016-06-13
145	SB170326	0	0	f	f	148500	f	14	3	f	f	Veruntreuung	0	https://www.gerichte-zh.ch/fileadmin/user_upload/entscheide/oeffentlich/SB170326-O1.pdf	Bezirksgericht Zürich	2	2017-06-28
147	SB170014	0	0	t	f	67187	f	10	0	t	t	Veruntreuung	2	https://entscheidsuche.ch/docs/ZH_Obergericht/ZH_OG_002_SF180003_2018-10-04.pdf	Bezirksgericht Zürich	2	2016-12-13
152	SB170390	0	0	f	t	9300000	f	48	5	f	f	Veruntreuung	2	https://www.gerichte-zh.ch/fileadmin/user_upload/entscheide/oeffentlich/SB170390-O2.pdf	Bezirksgericht Zürich	2	2017-07-20
149	SB160464	0	0	t	f	525000	f	18	0	t	f	Veruntreuung	0	https://www.gerichte-zh.ch/fileadmin/user_upload/entscheide/oeffentlich/SB160464-O1.pdf	Bezirksgericht Zürich	1	2016-10-05
150	SB150299	0	0	t	f	377400	f	12	0	f	f	Veruntreuung	0	https://www.gerichte-zh.ch/fileadmin/user_upload/entscheide/oeffentlich/SB150299-O1.pdf	Bezirksgericht Zürich	2	2015-06-09
151	SB130436	0	0	f	f	110000	f	9	2	f	f	Veruntreuung	0	https://www.gerichte-zh.ch/fileadmin/user_upload/entscheide/oeffentlich/SB130436-O1.pdf	Bezirksgericht Bülach	2	2013-09-04
153	SB220165	0	1	t	f	5829	f	7	1	t	t	betr. Missbrauch DVA	0	https://www.gerichte-zh.ch/fileadmin/user_upload/entscheide/oeffentlich/SB220165-O1.pdf	Bezirksgericht Winterthur	1	2021-06-03
154	SB150134	0	0	f	f	19038	f	5	1	f	f	ung. Geschäftsbesorgung	0	https://www.gerichte-zh.ch/fileadmin/user_upload/entscheide/oeffentlich/SB150134-O1.pdf	Bezirksgericht Winterthur	2	2015-01-20
155	SB160193	0	0	t	f	500000	f	20	8	t	t	Betrug	0	https://www.gerichte-zh.ch/fileadmin/user_upload/entscheide/oeffentlich/SB160193-O1.pdf	Bezirksgericht Zürich	2	2016-03-09
156	SB210192	0	0	f	t	640000	f	30	0	f	f	Betrug	1	https://www.gerichte-zh.ch/fileadmin/user_upload/entscheide/oeffentlich/SB210192-O1.pdf	Bezirksgericht Zürich	0	2020-12-17
157	SB220196	0	0	f	f	1950	f	10	2	t	t	Diebstahl	2	https://www.gerichte-zh.ch/fileadmin/user_upload/entscheide/oeffentlich/SB220196-O1.pdf	Bezirksgericht Winterthur	1	2021-08-30
158	SB210319	0	0	t	t	190000	f	36	6	f	f	Diebstahl	2	https://www.gerichte-zh.ch/fileadmin/user_upload/entscheide/oeffentlich/SB210319-O1.pdf	Bezirksgericht Dietikon	1	2020-11-11
160	SB120055	0	0	t	f	8131	f	7	1	f	f	Veruntreuung	0	https://www.gerichte-zh.ch/fileadmin/user_upload/entscheide/oeffentlich/SB120055-O1.pdf	Bezirksgericht Zürich	2	2011-12-05
161	SB160371	0	0	t	f	8000000	f	66	4	t	f	Veruntreuung	2	https://www.gerichte-zh.ch/fileadmin/user_upload/entscheide/oeffentlich/SB160371-O2.pdf	Bezirksgericht Zürich	2	2016-06-04
162	SB150164	0	0	f	f	90000	f	10	0	t	f	ung. Geschäftsbesorgung	2	https://www.gerichte-zh.ch/fileadmin/user_upload/entscheide/oeffentlich/SB150164-O1.pdf	Bezirksgericht Winterthur	2	2014-12-04
163	SB170098	0	0	t	f	50001	f	11	3	f	f	Veruntreuung	0	https://www.gerichte-zh.ch/fileadmin/user_upload/entscheide/oeffentlich/SB170098-O1.pdf	Bezirksgericht Zürich	2	2016-11-30
164	SB200223	0	1	f	f	430	f	9	5	t	t	Veruntreuung	2	https://www.gerichte-zh.ch/fileadmin/user_upload/entscheide/oeffentlich/SB200223-O1.pdf	Bezirksgericht Winterthur	2	2019-12-12
165	SB110334	0	0	t	f	63432	f	26	0	t	t	Veruntreuung	2	https://www.gerichte-zh.ch/fileadmin/user_upload/entscheide/oeffentlich/SB110334-O1.pdf	Bezirksgericht Zürich	2	2010-10-07
166	SB160202	0	0	t	f	299999	f	40	2	f	f	Veruntreuung	2	https://www.gerichte-zh.ch/fileadmin/user_upload/entscheide/oeffentlich/SB160202-O1.pdf	Bezirksgericht Zürich	2	2016-02-11
167	SB150326	0	0	t	f	3000	f	12	10	f	f	Veruntreuung	0	https://www.gerichte-zh.ch/fileadmin/user_upload/entscheide/oeffentlich/SB150326-O1.pdf	Bezirksgericht Hinwil	2	2015-07-07
168	SB210518	0	0	f	f	608400	f	39	4	t	f	Veruntreuung	2	https://www.gerichte-zh.ch/fileadmin/user_upload/entscheide/oeffentlich/SB150326-O1.pdf	Bezirksgericht Bülach	2	2021-04-10
159	SB210321	0	0	t	t	630000	f	24	0	f	f	Veruntreuung	0	https://www.gerichte-zh.ch/fileadmin/user_upload/entscheide/oeffentlich/SB210321-O1.pdf	Bezirksgericht Zürich	2	2021-03-10
170	SB170011	0	1	f	f	1800000	f	30	0	f	f	Diebstahl	1	https://www.gerichte-zh.ch/fileadmin/user_upload/entscheide/oeffentlich/SB170011-O1.pdf	Bezirksgericht Zürich	1	2016-10-26
171	SB170010	0	0	f	f	1800000	f	39	0	t	t	Diebstahl	2	https://www.gerichte-zh.ch/fileadmin/user_upload/entscheide/oeffentlich/SB170010-O1.pdf	Bezirksgericht Zürich	1	2016-10-26
172	SB170047	0	0	f	f	415	f	3	0	t	t	Diebstahl	2	https://www.gerichte-zh.ch/fileadmin/user_upload/entscheide/oeffentlich/SB170047-O1.pdf	Bezirksgericht Bülach	1	2016-12-09
173	SB210222	0	1	f	f	418	f	1	0	f	f	Diebstahl	0	https://www.gerichte-zh.ch/fileadmin/user_upload/entscheide/oeffentlich/SB210222-O1.pdf	Bezirksgericht Bülach	2	2021-01-06
148	SB160468	0	0	f	t	178000	f	12	0	f	f	Veruntreuung	0	https://www.gerichte-zh.ch/fileadmin/user_upload/entscheide/oeffentlich/SB160468-O1.pdf	Bezirksgericht Zürich	2	2016-06-24
175	SB160078	0	0	f	f	7280	f	8	1	t	t	Betrug	0	https://www.gerichte-zh.ch/fileadmin/user_upload/entscheide/oeffentlich/SB160078-O1.pdf	Bezirksgericht Zürich	2	2015-12-11
176	SB160287	0	0	t	f	102000	f	42	5	t	t	Diebstahl	2	https://www.gerichte-zh.ch/fileadmin/user_upload/entscheide/oeffentlich/SB160286-O1.pdf	Bezirksgericht Horgen	1	2016-02-19
177	SB160286	0	0	t	f	102000	t	40	12	t	t	Diebstahl	2	https://www.gerichte-zh.ch/fileadmin/user_upload/entscheide/oeffentlich/SB160286-O1.pdf	Bezirksgericht Uster	1	2016-02-19
178	SB170314	0	1	f	f	1340	f	4	2	f	f	Diebstahl	0	https://www.gerichte-zh.ch/fileadmin/user_upload/entscheide/oeffentlich/SB170314-O1.pdf	Bezirksgericht Zürich	1	2017-07-21
174	SB160244	0	1	f	f	87352	f	10	2	t	t	Diebstahl	2	https://www.gerichte-zh.ch/fileadmin/user_upload/entscheide/oeffentlich/SB160244-O1.pdf	Bezirksgericht Hinwil	1	2016-03-02
179	SB130181	0	0	t	f	28222	f	6	4	f	f	Diebstahl	0	https://www.gerichte-zh.ch/fileadmin/user_upload/entscheide/oeffentlich/SB130181-O2.pdf	Bezirksgericht Uster	1	2013-01-24
180	SB110685	0	0	f	f	25700	f	10	4	t	t	Diebstahl	2	https://www.gerichte-zh.ch/fileadmin/user_upload/entscheide/oeffentlich/SB110685-O1.pdf	Bezirksgericht Bülach	2	2011-07-25
146	SB170180	0	0	f	t	6000000	f	42	0	f	f	Veruntreuung	2	https://www.gerichte-zh.ch/fileadmin/user_upload/entscheide/oeffentlich/SB170180-O1.pdf	Bezirksgericht Zürich	0	2017-02-01
169	SB180030	0	1	t	t	4097832	f	32	3	f	f	Veruntreuung	1	https://www.gerichte-zh.ch/fileadmin/user_upload/entscheide/oeffentlich/SB180030-O1.pdf	Bezirksgericht Zürich	2	2017-11-10
181	SB110028	0	0	f	f	2900000	f	36	0	f	f	ung. Geschäftsbesorgung	1	https://www.gerichte-zh.ch/fileadmin/user_upload/entscheide/oeffentlich/SB110028-O1.pdf	Bezirksgericht Zürich	2	2010-10-03
182	SB110525	0	0	f	f	17575	f	8	2	t	f	ung. Geschäftsbesorgung	0	https://www.gerichte-zh.ch/fileadmin/user_upload/entscheide/oeffentlich/SB110525-O1.pdf	Bezirksgericht Zürich	2	2011-06-22
183	SB180513	0	0	f	f	2674	f	7	4	t	f	ung. Geschäftsbesorgung	0	https://www.gerichte-zh.ch/fileadmin/user_upload/entscheide/oeffentlich/SB180513-O1.pdf	Bezirksgericht Päffikon	2	2018-07-20
184	SB110042	0	0	t	f	1500000	f	24	0	f	f	ung. Geschäftsbesorgung	0	https://www.gerichte-zh.ch/fileadmin/user_upload/entscheide/oeffentlich/SB110042-O1.pdf	Bezirksgericht Zürich	2	2009-06-17
185	SB110254	0	0	t	f	120000	f	9	6	f	f	ung. Geschäftsbesorgung	0	https://www.gerichte-zh.ch/fileadmin/user_upload/entscheide/oeffentlich/SB110254-O1.pdf	Bezirksgericht Zürich	2	2010-12-08
186	SB140214	0	0	t	f	6000000	f	42	3	t	f	Veruntreuung	2	https://www.gerichte-zh.ch/fileadmin/user_upload/entscheide/oeffentlich/SB140214-O1.pdf	Bezirksgericht Zürich	2	2014-04-04
187	SB200075	0	0	f	t	163284	f	36	14	f	f	Betrug	1	https://www.gerichte-zh.ch/fileadmin/user_upload/entscheide/oeffentlich/SB200075-O1.pdf	Bezirksgericht Uster	2	2019-11-14
188	SB140292	0	0	f	f	100000	f	15	0	f	f	ung. Geschäftsbesorgung	0	https://www.gerichte-zh.ch/fileadmin/user_upload/entscheide/oeffentlich/SB140292-O1.pdf	Bezirksgericht Zürich	2	2014-05-22
189	SB110305	0	0	f	t	13700000	f	36	6	t	t	Betrug	1	https://www.gerichte-zh.ch/fileadmin/user_upload/entscheide/oeffentlich/SB110305-O2.pdf	Bezirksgericht Meilen	2	2011-03-15
\.


--
-- Data for Name: django_admin_log; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.django_admin_log (id, action_time, object_id, object_repr, action_flag, change_message, content_type_id, user_id) FROM stdin;
1	2021-12-22 08:28:32.081871+00	48	Urteil object (48)	3		7	1
2	2022-10-28 19:55:54.482667+00	108	TestSachbeschae	3		7	1
3	2022-10-28 19:55:54.503138+00	107	testDiebstahl	3		7	1
4	2023-03-01 11:26:38.654063+00	1	Beispielurteile	1	[{"added": {}}]	9	1
5	2023-03-01 14:53:50.72409+00	1	random	3		8	1
6	2023-03-01 15:22:39.239502+00	2	random	3		8	1
7	2023-03-01 15:53:35.66423+00	3	random	3		8	1
8	2023-03-13 10:09:58.681517+00	7	rf_regr_all	3		8	1
9	2023-03-13 10:09:58.684373+00	6	lr_regr_all	3		8	1
10	2023-03-13 10:09:58.686062+00	5	rf_regr_all	3		8	1
11	2023-03-13 10:09:58.687361+00	4	random	3		8	1
12	2023-03-13 22:19:00.085038+00	7	SB200188	3		7	1
\.


--
-- Data for Name: django_content_type; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.django_content_type (id, app_label, model) FROM stdin;
1	admin	logentry
2	auth	permission
3	auth	group
4	auth	user
5	contenttypes	contenttype
6	sessions	session
7	database	urteil
8	database	kimodelpicklefile
9	database	diagrammsvg
\.


--
-- Data for Name: django_migrations; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.django_migrations (id, app, name, applied) FROM stdin;
1	contenttypes	0001_initial	2021-10-22 19:39:10.020151+00
2	auth	0001_initial	2021-10-22 19:39:10.209797+00
3	admin	0001_initial	2021-10-22 19:39:10.247446+00
4	admin	0002_logentry_remove_auto_add	2021-10-22 19:39:10.260464+00
5	admin	0003_logentry_add_action_flag_choices	2021-10-22 19:39:10.272388+00
6	contenttypes	0002_remove_content_type_name	2021-10-22 19:39:10.298724+00
7	auth	0002_alter_permission_name_max_length	2021-10-22 19:39:10.314999+00
8	auth	0003_alter_user_email_max_length	2021-10-22 19:39:10.33207+00
9	auth	0004_alter_user_username_opts	2021-10-22 19:39:10.345613+00
10	auth	0005_alter_user_last_login_null	2021-10-22 19:39:10.361553+00
11	auth	0006_require_contenttypes_0002	2021-10-22 19:39:10.367786+00
12	auth	0007_alter_validators_add_error_messages	2021-10-22 19:39:10.381255+00
13	auth	0008_alter_user_username_max_length	2021-10-22 19:39:10.400305+00
14	auth	0009_alter_user_last_name_max_length	2021-10-22 19:39:10.419059+00
15	auth	0010_alter_group_name_max_length	2021-10-22 19:39:10.440907+00
16	auth	0011_update_proxy_permissions	2021-10-22 19:39:10.455024+00
17	auth	0012_alter_user_first_name_max_length	2021-10-22 19:39:10.469276+00
18	database	0001_initial	2021-10-22 19:39:10.486866+00
19	sessions	0001_initial	2021-10-22 19:39:10.513474+00
20	database	0002_auto_20211022_2002	2021-10-22 21:56:57.686576+00
21	database	0003_auto_20211023_2112	2021-11-02 20:55:56.704413+00
22	database	0004_auto_20211023_2116	2021-11-02 20:55:56.73115+00
23	database	0005_urteil_hauptdelikt	2021-11-02 20:55:56.773484+00
24	database	0006_alter_urteil_fall_nr	2022-01-23 22:13:06.302379+00
25	database	0007_urteil_vollzug	2022-01-23 22:13:06.337659+00
26	database	0008_auto_20220123_2241	2022-01-23 22:13:06.349866+00
27	database	0009_auto_20221029_1724	2022-10-29 22:22:39.589631+00
28	database	0009_auto_20221108_1927	2023-02-19 14:35:47.279424+00
29	database	0010_merge_0009_auto_20221029_1724_0009_auto_20221108_1927	2023-02-19 14:35:47.328331+00
30	database	0011_auto_20230219_1604	2023-02-19 15:05:12.412162+00
31	database	0012_auto_20230225_2253	2023-02-28 23:09:58.646743+00
32	database	0013_auto_20230228_1259	2023-02-28 23:09:58.661044+00
33	database	0014_kimodelpicklefile_prognoseleistung_dict	2023-02-28 23:09:58.66957+00
34	database	0015_kimodelpicklefile_encoder	2023-03-20 22:26:04.391496+00
35	database	0016_auto_20230402_2122	2023-04-02 20:58:04.959896+00
36	database	0017_diagrammsvg_lesehinweis	2023-04-14 20:25:35.27381+00
\.


--
-- Data for Name: django_session; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.django_session (session_key, session_data, expire_date) FROM stdin;
b9i7rdl0buyr5s60ymcn5d5cx83gjftq	.eJxVjEEOwiAQRe_C2hCgIxWX7j0DmWEGqRpISrsy3l2bdKHb_977LxVxXUpcu8xxYnVWVh1-N8L0kLoBvmO9NZ1aXeaJ9KbonXZ9bSzPy-7-HRTs5Vs78BlPXsjmnDIMiN6MyIwAHsSJC8Emy2DRsKRjoETDKGyExCPboN4fDIo5QQ:1ndevY:7uBmfMJDWh7BmFp7bhesDMiH0w5zJ1bFwCUhqjXgT9I	2022-04-24 21:16:56.201615+00
00syc4bqxuhphhmsoq63rm982jzyd8es	.eJxVjEEOwiAQRe_C2hCgIxWX7j0DmWEGqRpISrsy3l2bdKHb_977LxVxXUpcu8xxYnVWVh1-N8L0kLoBvmO9NZ1aXeaJ9KbonXZ9bSzPy-7-HRTs5Vs78BlPXsjmnDIMiN6MyIwAHsSJC8Emy2DRsKRjoETDKGyExCPboN4fDIo5QQ:1ndo6A:YgQ6hur8FaxlvBkIE7Kpi-RMNtnOhUPvfAvsX4-BxyM	2022-04-25 07:04:30.41727+00
mp6eare7pmtj91aiuqlzosgi50reufpo	.eJxVjEEOwiAQRe_C2hCgIxWX7j0DmWEGqRpISrsy3l2bdKHb_977LxVxXUpcu8xxYnVWVh1-N8L0kLoBvmO9NZ1aXeaJ9KbonXZ9bSzPy-7-HRTs5Vs78BlPXsjmnDIMiN6MyIwAHsSJC8Emy2DRsKRjoETDKGyExCPboN4fDIo5QQ:1nmtpk:O7QVa14dIEIKw4vdzzDBwlPe7Nc7DCyZHHbG8UaCggU	2022-05-20 09:01:08.577762+00
u1jyiahlptd7ifcjckwckhhgjix3wcva	.eJxVjEEOwiAQRe_C2hCgIxWX7j0DmWEGqRpISrsy3l2bdKHb_977LxVxXUpcu8xxYnVWVh1-N8L0kLoBvmO9NZ1aXeaJ9KbonXZ9bSzPy-7-HRTs5Vs78BlPXsjmnDIMiN6MyIwAHsSJC8Emy2DRsKRjoETDKGyExCPboN4fDIo5QQ:1nyp1Q:aG7qjN8qhp3S6dhs6E6pFwsliqcL0Pn1k1xjmhv4F9k	2022-06-22 06:18:28.962893+00
yb9teyqoj0sggvutobz16116jboc4mm8	.eJxVjEEOwiAQRe_C2hCgIxWX7j0DmWEGqRpISrsy3l2bdKHb_977LxVxXUpcu8xxYnVWVh1-N8L0kLoBvmO9NZ1aXeaJ9KbonXZ9bSzPy-7-HRTs5Vs78BlPXsjmnDIMiN6MyIwAHsSJC8Emy2DRsKRjoETDKGyExCPboN4fDIo5QQ:1oB7n3:gQ2lOIchf_u5rDTllaLR8Gob18a01ccoBzn3zRo4ljc	2022-07-26 04:46:29.922987+00
dgz2yw60zne5mbxjuxzsaicjyqb12td7	.eJxVjEEOwiAQRe_C2hCgIxWX7j0DmWEGqRpISrsy3l2bdKHb_977LxVxXUpcu8xxYnVWVh1-N8L0kLoBvmO9NZ1aXeaJ9KbonXZ9bSzPy-7-HRTs5Vs78BlPXsjmnDIMiN6MyIwAHsSJC8Emy2DRsKRjoETDKGyExCPboN4fDIo5QQ:1oIos4:NdmhES1eJFGTOJx_jXWLEs1EFg97QRiySo0l1uNi9Qo	2022-08-16 10:11:28.382799+00
myh7hczpyp28mn20f0ok9t0acc742goq	.eJxVjEEOwiAQRe_C2hCgIxWX7j0DmWEGqRpISrsy3l2bdKHb_977LxVxXUpcu8xxYnVWVh1-N8L0kLoBvmO9NZ1aXeaJ9KbonXZ9bSzPy-7-HRTs5Vs78BlPXsjmnDIMiN6MyIwAHsSJC8Emy2DRsKRjoETDKGyExCPboN4fDIo5QQ:1oOgoD:UqtMPISIyJk_sD9tBZp5x9e6Q2zHbRIIa76C6bu0GLk	2022-09-01 14:47:45.947195+00
a0v1mn04ft9jbafu3jyhfv28lh4o08oi	.eJxVjEEOwiAQRe_C2hCgIxWX7j0DmWEGqRpISrsy3l2bdKHb_977LxVxXUpcu8xxYnVWVh1-N8L0kLoBvmO9NZ1aXeaJ9KbonXZ9bSzPy-7-HRTs5Vs78BlPXsjmnDIMiN6MyIwAHsSJC8Emy2DRsKRjoETDKGyExCPboN4fDIo5QQ:1obKeH:rV-_Bl61FRpyL2-4FuXIXEs8V4NbpY8cZtZ4vLerQ2o	2022-10-06 11:45:45.957139+00
a8oh7ekhtdape2tm2mjsrvae70kwln7w	.eJxVjEEOwiAQRe_C2hCgIxWX7j0DmWEGqRpISrsy3l2bdKHb_977LxVxXUpcu8xxYnVWVh1-N8L0kLoBvmO9NZ1aXeaJ9KbonXZ9bSzPy-7-HRTs5Vs78BlPXsjmnDIMiN6MyIwAHsSJC8Emy2DRsKRjoETDKGyExCPboN4fDIo5QQ:1obUdY:bq_jUS_kuZfHSwccsv5_ytHc3w6JUcRUsl_EsXWTTBc	2022-10-06 22:25:40.590841+00
25z8zf6vo80xofl7pn5tmj1fmd3nx0pc	.eJxVjEEOwiAQRe_C2hCgIxWX7j0DmWEGqRpISrsy3l2bdKHb_977LxVxXUpcu8xxYnVWVh1-N8L0kLoBvmO9NZ1aXeaJ9KbonXZ9bSzPy-7-HRTs5Vs78BlPXsjmnDIMiN6MyIwAHsSJC8Emy2DRsKRjoETDKGyExCPboN4fDIo5QQ:1ol9B3:Oxvc2Cv9dyczA0eMTR5WRCaUdEWbpybyXV0sUCqCEHU	2022-11-02 13:32:09.539661+00
b3z6qetwzums9c90djsae5oleip72bkm	.eJxVjEEOwiAQRe_C2hCgIxWX7j0DmWEGqRpISrsy3l2bdKHb_977LxVxXUpcu8xxYnVWVh1-N8L0kLoBvmO9NZ1aXeaJ9KbonXZ9bSzPy-7-HRTs5Vs78BlPXsjmnDIMiN6MyIwAHsSJC8Emy2DRsKRjoETDKGyExCPboN4fDIo5QQ:1ooVSy:YgZwzgqz7Pi-7A_CeB2cJvT6MLX8N0gb0HXs-FIfTA4	2022-11-11 19:56:32.263446+00
4n4k8oiyep9737bggbuk17c9ebi1h1h7	.eJxVjEEOwiAQRe_C2hCgIxWX7j0DmWEGqRpISrsy3l2bdKHb_977LxVxXUpcu8xxYnVWVh1-N8L0kLoBvmO9NZ1aXeaJ9KbonXZ9bSzPy-7-HRTs5Vs78BlPXsjmnDIMiN6MyIwAHsSJC8Emy2DRsKRjoETDKGyExCPboN4fDIo5QQ:1oouRa:nmwffWO_7785WeQ9Dd2-r_0Yi51L29RE8LiU8cgmsd4	2022-11-12 22:36:46.14594+00
jwfl472o62u17dnp1sp03w42jawcx323	.eJxVjEEOwiAQRe_C2hCgIxWX7j0DmWEGqRpISrsy3l2bdKHb_977LxVxXUpcu8xxYnVWVh1-N8L0kLoBvmO9NZ1aXeaJ9KbonXZ9bSzPy-7-HRTs5Vs78BlPXsjmnDIMiN6MyIwAHsSJC8Emy2DRsKRjoETDKGyExCPboN4fDIo5QQ:1opRhT:GOWu1cggl03SyPWzhqdbqRnDeTxjh0fXkc57gc4tFqY	2022-11-14 10:07:23.337882+00
tch1ejc3j7499omfvz17fu3ud70zf7ax	.eJxVjEEOwiAQRe_C2hCgIxWX7j0DmWEGqRpISrsy3l2bdKHb_977LxVxXUpcu8xxYnVWVh1-N8L0kLoBvmO9NZ1aXeaJ9KbonXZ9bSzPy-7-HRTs5Vs78BlPXsjmnDIMiN6MyIwAHsSJC8Emy2DRsKRjoETDKGyExCPboN4fDIo5QQ:1ow2jN:5oP6R4JyzttvdTEW0Lx51hv7ZKDY1YyjTJMSGIMHnXc	2022-12-02 14:52:37.301195+00
0ljjf7dad5qr2ohkyawl7kipyg69o9q4	.eJxVjEEOwiAQRe_C2hCgIxWX7j0DmWEGqRpISrsy3l2bdKHb_977LxVxXUpcu8xxYnVWVh1-N8L0kLoBvmO9NZ1aXeaJ9KbonXZ9bSzPy-7-HRTs5Vs78BlPXsjmnDIMiN6MyIwAHsSJC8Emy2DRsKRjoETDKGyExCPboN4fDIo5QQ:1p2ooq:fVqhCvdr-z8xpHHBR4pkKb8FFErb-HsIcLMOuPbB6a0	2022-12-21 07:26:16.675441+00
ascn0by5d6m1ix7qt05x3pclglrt1c0i	.eJxVjDsOwjAQBe_iGlk2jn-U9DmDtev14gBypDipEHeHSCmgfTPzXiLBtta09bKkicRFaHH63RDyo7Qd0B3abZZ5busyodwVedAux5nK83q4fwcVev3WgQFL9p60iYOLKvpzDmCiLhiJgrLeYeDBZWUtMmdPbMiyDsaxsQji_QHtPzhT:1p2sbd:0-AiLb_3v8a3gOdpVtNQHTd9xSi0-MNAegTq6gmj8mY	2022-12-21 11:28:53.72589+00
eyj7feh9nki3rs3cf5qby4ozp91ftqay	.eJxVjDsOwjAQBe_iGlk2jn-U9DmDtev14gBypDipEHeHSCmgfTPzXiLBtta09bKkicRFaHH63RDyo7Qd0B3abZZ5busyodwVedAux5nK83q4fwcVev3WgQFL9p60iYOLKvpzDmCiLhiJgrLeYeDBZWUtMmdPbMiyDsaxsQji_QHtPzhT:1pTlIH:1HWco5tChGh8eDOChlfRBlm7tNaWU6fs-85FOIWXT1Y	2023-03-05 15:08:01.126839+00
c220k52d2gu7sgtccjnbukvlkbiqgodu	.eJxVjDsOwjAQBe_iGlk2jn-U9DmDtev14gBypDipEHeHSCmgfTPzXiLBtta09bKkicRFaHH63RDyo7Qd0B3abZZ5busyodwVedAux5nK83q4fwcVev3WgQFL9p60iYOLKvpzDmCiLhiJgrLeYeDBZWUtMmdPbMiyDsaxsQji_QHtPzhT:1pTr8V:Kb3ytdKPRVk-6vM5xwDiqs0ESA6pYropfcodVTA2gUI	2023-03-05 21:22:19.873906+00
0m5nbqoop4keu06ro02g61wv7sqowmn8	.eJxVjEEOwiAQRe_C2hCgIxWX7j0DmWEGqRpISrsy3l2bdKHb_977LxVxXUpcu8xxYnVWVh1-N8L0kLoBvmO9NZ1aXeaJ9KbonXZ9bSzPy-7-HRTs5Vs78BlPXsjmnDIMiN6MyIwAHsSJC8Emy2DRsKRjoETDKGyExCPboN4fDIo5QQ:1pTruN:xyKkjF41FzapO8XZF80IoVMioYnNfYg-weei7CJHpmw	2023-03-05 22:11:47.734354+00
jm64qxsl1ooo159objwwl3w0y8zdf05r	.eJxVjEEOwiAQRe_C2hCgIxWX7j0DmWEGqRpISrsy3l2bdKHb_977LxVxXUpcu8xxYnVWVh1-N8L0kLoBvmO9NZ1aXeaJ9KbonXZ9bSzPy-7-HRTs5Vs78BlPXsjmnDIMiN6MyIwAHsSJC8Emy2DRsKRjoETDKGyExCPboN4fDIo5QQ:1pUE8R:flvjBPcoOTfMLYBanGGX9Za0qtY0xDyQKZxOn8RMJ9c	2023-03-06 21:55:47.173205+00
t0dtha68vbq75i651y0rgws8a8g2qv62	.eJxVjEEOwiAQRe_C2hCgIxWX7j0DmWEGqRpISrsy3l2bdKHb_977LxVxXUpcu8xxYnVWVh1-N8L0kLoBvmO9NZ1aXeaJ9KbonXZ9bSzPy-7-HRTs5Vs78BlPXsjmnDIMiN6MyIwAHsSJC8Emy2DRsKRjoETDKGyExCPboN4fDIo5QQ:1pVBqb:PZpCfkonKFl_L6g6_sFLDUBO_neVpgNxfDz4lpa69m8	2023-03-09 13:41:21.935922+00
fi1ego1747rbhr1uw8id7qa9oaf6itd2	.eJxVjEEOwiAQRe_C2hCgIxWX7j0DmWEGqRpISrsy3l2bdKHb_977LxVxXUpcu8xxYnVWVh1-N8L0kLoBvmO9NZ1aXeaJ9KbonXZ9bSzPy-7-HRTs5Vs78BlPXsjmnDIMiN6MyIwAHsSJC8Emy2DRsKRjoETDKGyExCPboN4fDIo5QQ:1pbehD:-o7svqaNHLNuNcTWdigyzhPhCCmU1rLH6-y1rj5dkEA	2023-03-27 09:42:23.389367+00
7at01c9k2hap65w7yjbzmf1smvmjphni	.eJxVjEEOwiAQRe_C2hCgIxWX7j0DmWEGqRpISrsy3l2bdKHb_977LxVxXUpcu8xxYnVWVh1-N8L0kLoBvmO9NZ1aXeaJ9KbonXZ9bSzPy-7-HRTs5Vs78BlPXsjmnDIMiN6MyIwAHsSJC8Emy2DRsKRjoETDKGyExCPboN4fDIo5QQ:1pbqVE:TUuoU8bXavDnGEG7jSGDqA8lOCLyMNRFN1HT2Tjuix4	2023-03-27 22:18:48.933904+00
tb79b912l9i3z2ou90wf3phtecrpipyl	.eJxVjEEOwiAQRe_C2hCgIxWX7j0DmWEGqRpISrsy3l2bdKHb_977LxVxXUpcu8xxYnVWVh1-N8L0kLoBvmO9NZ1aXeaJ9KbonXZ9bSzPy-7-HRTs5Vs78BlPXsjmnDIMiN6MyIwAHsSJC8Emy2DRsKRjoETDKGyExCPboN4fDIo5QQ:1pejYX:GordB4qaUic_MmMlfUF8ptGZ_V_fZtxFG9N5MO8OV3w	2023-04-04 21:30:09.56449+00
og9f5yvbkgnhyrpf044it2a68h3axdsk	.eJxVjEEOwiAQRe_C2hCgIxWX7j0DmWEGqRpISrsy3l2bdKHb_977LxVxXUpcu8xxYnVWVh1-N8L0kLoBvmO9NZ1aXeaJ9KbonXZ9bSzPy-7-HRTs5Vs78BlPXsjmnDIMiN6MyIwAHsSJC8Emy2DRsKRjoETDKGyExCPboN4fDIo5QQ:1pf6ma:SVi6X-y1_fyj5yidrxA7jTf0q0koTvWJKR2KZ-L5ikA	2023-04-05 22:18:12.592856+00
i6y5wms2r7vm2ljpwa8r2crs7qncddi0	.eJxVjEEOwiAQRe_C2hCgIxWX7j0DmWEGqRpISrsy3l2bdKHb_977LxVxXUpcu8xxYnVWVh1-N8L0kLoBvmO9NZ1aXeaJ9KbonXZ9bSzPy-7-HRTs5Vs78BlPXsjmnDIMiN6MyIwAHsSJC8Emy2DRsKRjoETDKGyExCPboN4fDIo5QQ:1pn2w4:jmng0CLOiWGcc-7U_RLQzwcNHWtsJFWVybTo7SwUPPc	2023-04-27 19:48:48.028183+00
ejph3q6a0wpshewrivrq4es60gxdyrhw	.eJxVjEEOwiAQRe_C2hCgIxWX7j0DmWEGqRpISrsy3l2bdKHb_977LxVxXUpcu8xxYnVWVh1-N8L0kLoBvmO9NZ1aXeaJ9KbonXZ9bSzPy-7-HRTs5Vs78BlPXsjmnDIMiN6MyIwAHsSJC8Emy2DRsKRjoETDKGyExCPboN4fDIo5QQ:1pnaAr:WTzt38f3UZuDx4b2XPmK7BEGkyz4ClAYFdMRLYXfkek	2023-04-29 07:18:17.650809+00
\.


--
-- Name: auth_group_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.auth_group_id_seq', 1, false);


--
-- Name: auth_group_permissions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.auth_group_permissions_id_seq', 1, false);


--
-- Name: auth_permission_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.auth_permission_id_seq', 36, true);


--
-- Name: auth_user_groups_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.auth_user_groups_id_seq', 1, false);


--
-- Name: auth_user_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.auth_user_id_seq', 1, true);


--
-- Name: auth_user_user_permissions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.auth_user_user_permissions_id_seq', 1, false);


--
-- Name: database_diagrammsvg_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.database_diagrammsvg_id_seq', 8, true);


--
-- Name: database_kimodelpicklefile_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.database_kimodelpicklefile_id_seq', 11, true);


--
-- Name: database_urteil_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.database_urteil_id_seq', 189, true);


--
-- Name: django_admin_log_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.django_admin_log_id_seq', 12, true);


--
-- Name: django_content_type_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.django_content_type_id_seq', 9, true);


--
-- Name: django_migrations_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.django_migrations_id_seq', 36, true);


--
-- Name: auth_group auth_group_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auth_group
    ADD CONSTRAINT auth_group_name_key UNIQUE (name);


--
-- Name: auth_group_permissions auth_group_permissions_group_id_permission_id_0cd325b0_uniq; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auth_group_permissions
    ADD CONSTRAINT auth_group_permissions_group_id_permission_id_0cd325b0_uniq UNIQUE (group_id, permission_id);


--
-- Name: auth_group_permissions auth_group_permissions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auth_group_permissions
    ADD CONSTRAINT auth_group_permissions_pkey PRIMARY KEY (id);


--
-- Name: auth_group auth_group_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auth_group
    ADD CONSTRAINT auth_group_pkey PRIMARY KEY (id);


--
-- Name: auth_permission auth_permission_content_type_id_codename_01ab375a_uniq; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auth_permission
    ADD CONSTRAINT auth_permission_content_type_id_codename_01ab375a_uniq UNIQUE (content_type_id, codename);


--
-- Name: auth_permission auth_permission_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auth_permission
    ADD CONSTRAINT auth_permission_pkey PRIMARY KEY (id);


--
-- Name: auth_user_groups auth_user_groups_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auth_user_groups
    ADD CONSTRAINT auth_user_groups_pkey PRIMARY KEY (id);


--
-- Name: auth_user_groups auth_user_groups_user_id_group_id_94350c0c_uniq; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auth_user_groups
    ADD CONSTRAINT auth_user_groups_user_id_group_id_94350c0c_uniq UNIQUE (user_id, group_id);


--
-- Name: auth_user auth_user_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auth_user
    ADD CONSTRAINT auth_user_pkey PRIMARY KEY (id);


--
-- Name: auth_user_user_permissions auth_user_user_permissions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auth_user_user_permissions
    ADD CONSTRAINT auth_user_user_permissions_pkey PRIMARY KEY (id);


--
-- Name: auth_user_user_permissions auth_user_user_permissions_user_id_permission_id_14a6b632_uniq; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auth_user_user_permissions
    ADD CONSTRAINT auth_user_user_permissions_user_id_permission_id_14a6b632_uniq UNIQUE (user_id, permission_id);


--
-- Name: auth_user auth_user_username_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auth_user
    ADD CONSTRAINT auth_user_username_key UNIQUE (username);


--
-- Name: database_diagrammsvg database_diagrammsvg_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.database_diagrammsvg
    ADD CONSTRAINT database_diagrammsvg_pkey PRIMARY KEY (id);


--
-- Name: database_kimodelpicklefile database_kimodelpicklefile_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.database_kimodelpicklefile
    ADD CONSTRAINT database_kimodelpicklefile_pkey PRIMARY KEY (id);


--
-- Name: database_urteil database_urteil_fall_nr_3140ccd2_uniq; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.database_urteil
    ADD CONSTRAINT database_urteil_fall_nr_3140ccd2_uniq UNIQUE (fall_nr);


--
-- Name: database_urteil database_urteil_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.database_urteil
    ADD CONSTRAINT database_urteil_pkey PRIMARY KEY (id);


--
-- Name: django_admin_log django_admin_log_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.django_admin_log
    ADD CONSTRAINT django_admin_log_pkey PRIMARY KEY (id);


--
-- Name: django_content_type django_content_type_app_label_model_76bd3d3b_uniq; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.django_content_type
    ADD CONSTRAINT django_content_type_app_label_model_76bd3d3b_uniq UNIQUE (app_label, model);


--
-- Name: django_content_type django_content_type_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.django_content_type
    ADD CONSTRAINT django_content_type_pkey PRIMARY KEY (id);


--
-- Name: django_migrations django_migrations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.django_migrations
    ADD CONSTRAINT django_migrations_pkey PRIMARY KEY (id);


--
-- Name: django_session django_session_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.django_session
    ADD CONSTRAINT django_session_pkey PRIMARY KEY (session_key);


--
-- Name: auth_group_name_a6ea08ec_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX auth_group_name_a6ea08ec_like ON public.auth_group USING btree (name varchar_pattern_ops);


--
-- Name: auth_group_permissions_group_id_b120cbf9; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX auth_group_permissions_group_id_b120cbf9 ON public.auth_group_permissions USING btree (group_id);


--
-- Name: auth_group_permissions_permission_id_84c5c92e; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX auth_group_permissions_permission_id_84c5c92e ON public.auth_group_permissions USING btree (permission_id);


--
-- Name: auth_permission_content_type_id_2f476e4b; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX auth_permission_content_type_id_2f476e4b ON public.auth_permission USING btree (content_type_id);


--
-- Name: auth_user_groups_group_id_97559544; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX auth_user_groups_group_id_97559544 ON public.auth_user_groups USING btree (group_id);


--
-- Name: auth_user_groups_user_id_6a12ed8b; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX auth_user_groups_user_id_6a12ed8b ON public.auth_user_groups USING btree (user_id);


--
-- Name: auth_user_user_permissions_permission_id_1fbb5f2c; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX auth_user_user_permissions_permission_id_1fbb5f2c ON public.auth_user_user_permissions USING btree (permission_id);


--
-- Name: auth_user_user_permissions_user_id_a95ead1b; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX auth_user_user_permissions_user_id_a95ead1b ON public.auth_user_user_permissions USING btree (user_id);


--
-- Name: auth_user_username_6821ab7c_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX auth_user_username_6821ab7c_like ON public.auth_user USING btree (username varchar_pattern_ops);


--
-- Name: database_urteil_fall_nr_3140ccd2_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX database_urteil_fall_nr_3140ccd2_like ON public.database_urteil USING btree (fall_nr varchar_pattern_ops);


--
-- Name: django_admin_log_content_type_id_c4bce8eb; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX django_admin_log_content_type_id_c4bce8eb ON public.django_admin_log USING btree (content_type_id);


--
-- Name: django_admin_log_user_id_c564eba6; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX django_admin_log_user_id_c564eba6 ON public.django_admin_log USING btree (user_id);


--
-- Name: django_session_expire_date_a5c62663; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX django_session_expire_date_a5c62663 ON public.django_session USING btree (expire_date);


--
-- Name: django_session_session_key_c0390e0f_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX django_session_session_key_c0390e0f_like ON public.django_session USING btree (session_key varchar_pattern_ops);


--
-- Name: auth_group_permissions auth_group_permissio_permission_id_84c5c92e_fk_auth_perm; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auth_group_permissions
    ADD CONSTRAINT auth_group_permissio_permission_id_84c5c92e_fk_auth_perm FOREIGN KEY (permission_id) REFERENCES public.auth_permission(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: auth_group_permissions auth_group_permissions_group_id_b120cbf9_fk_auth_group_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auth_group_permissions
    ADD CONSTRAINT auth_group_permissions_group_id_b120cbf9_fk_auth_group_id FOREIGN KEY (group_id) REFERENCES public.auth_group(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: auth_permission auth_permission_content_type_id_2f476e4b_fk_django_co; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auth_permission
    ADD CONSTRAINT auth_permission_content_type_id_2f476e4b_fk_django_co FOREIGN KEY (content_type_id) REFERENCES public.django_content_type(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: auth_user_groups auth_user_groups_group_id_97559544_fk_auth_group_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auth_user_groups
    ADD CONSTRAINT auth_user_groups_group_id_97559544_fk_auth_group_id FOREIGN KEY (group_id) REFERENCES public.auth_group(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: auth_user_groups auth_user_groups_user_id_6a12ed8b_fk_auth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auth_user_groups
    ADD CONSTRAINT auth_user_groups_user_id_6a12ed8b_fk_auth_user_id FOREIGN KEY (user_id) REFERENCES public.auth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: auth_user_user_permissions auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auth_user_user_permissions
    ADD CONSTRAINT auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm FOREIGN KEY (permission_id) REFERENCES public.auth_permission(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: auth_user_user_permissions auth_user_user_permissions_user_id_a95ead1b_fk_auth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auth_user_user_permissions
    ADD CONSTRAINT auth_user_user_permissions_user_id_a95ead1b_fk_auth_user_id FOREIGN KEY (user_id) REFERENCES public.auth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: django_admin_log django_admin_log_content_type_id_c4bce8eb_fk_django_co; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.django_admin_log
    ADD CONSTRAINT django_admin_log_content_type_id_c4bce8eb_fk_django_co FOREIGN KEY (content_type_id) REFERENCES public.django_content_type(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: django_admin_log django_admin_log_user_id_c564eba6_fk_auth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.django_admin_log
    ADD CONSTRAINT django_admin_log_user_id_c564eba6_fk_auth_user_id FOREIGN KEY (user_id) REFERENCES public.auth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- PostgreSQL database dump complete
--

