# This code is a translation to python from pg_key.c and pg_show.c released in the public domain by Michel Van den Bergh.
# http://alpha.uhasselt.be/Research/Algebra/Toga

import os
import random

from Code import ControlPosicion
from Code import Util
from Code import VarGen


class ListaLibros:
    def __init__(self):
        self.lista = []
        self.path = ""

        # S = Gestor solo
        # P = PGN
        # M = EntMaquina
        # T = Tutor
        self._modoAnalisis = ""

        self.alMenosUno()

    def recuperaVar(self, fichero):
        ll = Util.recuperaVar(fichero)
        if ll:
            self.lista = ll.lista
            self.path = ll.path
            self._modoAnalisis = ll._modoAnalisis
            self.alMenosUno()

    def guardaVar(self, fichero):
        Util.guardaVar(fichero, self)

    def alMenosUno(self):
        if len(self.lista) == 0:
            bookdef = VarGen.tbook
            b = Libro("P", bookdef.split("/")[1][:-4], bookdef, True)
            self.lista.append(b)

    def modoAnalisis(self, apli):
        return apli in self._modoAnalisis

    def porDefecto(self, book=None):
        if book:
            for book1 in self.lista:
                book1.pordefecto = False
            book.pordefecto = True
        else:
            self.alMenosUno()
            for book in self.lista:
                if book.pordefecto:
                    return book
            return self.lista[0]

    def cambiaModo(self, apli):
        if apli in self._modoAnalisis:
            self._modoAnalisis = self._modoAnalisis.replace(apli, "")
        else:
            self._modoAnalisis += apli

    def leeLibros(self, liLibros, fen, masTitulo, siPV):

        if not fen:
            return []

        posicion = ControlPosicion.ControlPosicion()
        posicion.leeFen(fen)
        p = Polyglot()
        ico = "w" if posicion.siBlancas else "b"
        icoL = "l"

        liResp = []
        for libro in liLibros:
            liResp.append((None, libro.nombre + masTitulo, icoL))
            li = p.lista(libro.path, fen)
            if li:
                total = 0
                for entry in li:
                    total += entry.weight

                for entry in li:
                    pv = entry.pv()
                    w = entry.weight
                    pc = w * 100.0 / total if total else "?"
                    pgn = posicion.pgnSP(pv[:2], pv[2:4], pv[4:])
                    liResp.append((pv if siPV else None, "%-5s -%7.02f%% -%7d" % (pgn, pc, w), ico))
            else:
                liResp.append((None, _("No result"), "c"))

        return liResp

    def comprueba(self):
        for x in range(len(self.lista) - 1, -1, -1):
            libro = self.lista[x]
            if not libro.existe():
                del self.lista[x]
        self.alMenosUno()

    def nuevo(self, libro):
        for libroA in self.lista:
            if libroA.igualque(libro):
                return
        self.lista.append(libro)

    def borra(self, libro):
        for n, libroL in enumerate(self.lista):
            if libroL == libro:
                del self.lista[n]

    def compruebaApertura(self, partida):
        liLibros = [libro for libro in self.lista if libro.pordefecto]
        if (not liLibros) and self.lista:
            liLibros = [self.lista[0]]

        p = Polyglot()
        icoL = "l"

        liResp = []
        for nlibro, libro in enumerate(liLibros):
            liResp.append((None, libro.nombre, icoL, None))
            for njug, jg in enumerate(partida.liJugadas):
                posicion = jg.posicionBase
                li = p.lista(libro.path, posicion.fen())
                if li:
                    total = 0
                    for entry in li:
                        total += entry.weight
                    pv = jg.movimiento()

                    ok = False

                    liOp = []
                    for entry in li:
                        w = entry.weight
                        pct = w * 100.0 / total if total else "-"
                        pvt = entry.pv()
                        pgn = posicion.pgnSP(pvt[:2], pvt[2:4], pvt[4:])
                        liOp.append("%-5s -%7.02f%% -%7d" % (pgn, pct, w))
                        if pv == pvt:
                            ok = True
                            pc = pct

                    if jg.posicionBase.siBlancas:
                        ico = "w"
                        previo = "%2d." % partida.numJugadaPGN(njug)
                        posterior = "   "
                    else:
                        ico = "b"
                        previo = "      "
                        posterior = ""
                    pgn = jg.pgnSP()
                    puntos = "%7.02f%%" % pc if ok else "   ???"

                    liResp.append(
                            ("%d|%d" % (nlibro, njug), "%s%-5s%s - %s" % (previo, pgn, posterior, puntos), ico, liOp))
                    if not ok:
                        break

        return liResp


class Libro:
    def __init__(self, tipo, nombre, path, pordefecto, extras=None):
        self.tipo = tipo
        self.nombre = nombre
        self.path = path
        self.pordefecto = pordefecto
        self.orden = 100  # futuro ?
        self.extras = extras  # futuro ?

    def igualque(self, otro):
        return self.tipo == otro.tipo and \
               self.nombre == otro.nombre and \
               self.path == otro.path

    def existe(self):
        return os.path.isfile(self.path)

    def polyglot(self):
        self.book = Polyglot()

    def miraListaJugadas(self, fen):
        li = self.book.lista(self.path, fen)
        posicion = ControlPosicion.ControlPosicion()
        posicion.leeFen(fen)

        total = 0
        maxim = 0
        for entry in li:
            w = entry.weight
            total += w
            if w > maxim:
                maxim = w

        listaJugadas = []
        for entry in li:
            pv = entry.pv()
            w = entry.weight
            pc = w * 100.0 / total if total else "?"
            desde, hasta, coronacion = pv[:2], pv[2:4], pv[4:]
            pgn = posicion.pgnSP(desde, hasta, coronacion)
            listaJugadas.append((desde, hasta, coronacion, "%-5s -%7.02f%% -%7d" % (pgn, pc, w), 1.0 * w / maxim))
        return listaJugadas

    def eligeJugadaTipo(self, fen, tipo):
        maxim = 0
        liMax = []
        li = self.book.lista(self.path, fen)
        nli = len(li)
        if nli == 0:
            return None

        elif nli == 1:
            pv = li[0].pv()

        elif tipo == "mp":  # Mejor posicion
            for entry in li:
                w = entry.weight
                if w > maxim:
                    maxim = w
                    liMax = [entry]
                elif w == maxim:
                    liMax.append(entry)
            pos = random.randint(0, len(liMax) - 1) if len(liMax) > 1 else 0
            pv = liMax[pos].pv()

        elif tipo == "au":  # Aleatorio uniforme
            pos = random.randint(0, len(li) - 1)
            pv = li[pos].pv()

        elif tipo == "ap":  # Aleatorio proporcional
            liW = [x.weight for x in li]
            t = sum(liW)
            num = random.randint(1, t)
            pos = 0
            t = 0
            for n, x in enumerate(liW):
                t += x
                if num <= t:
                    pos = n
                    break
            pv = li[pos].pv()

        else:
            return None

        return pv.lower()

    def miraListaPV(self, fen, siMax):
        li = self.book.lista(self.path, fen)

        liResp = []
        if siMax:
            maxim = -1
            for entry in li:
                w = entry.weight
                if w > maxim:
                    maxim = w
                    liResp = [entry.pv()]
                    # elif w == maxim:
                    # liResp.append(entry.pv())
        else:
            for entry in li:
                liResp.append(entry.pv())

        return liResp


class Entry:
    key = 0L
    move = 0L
    weight = 0L
    learn = 0L

    def pv(self):
        move = self.move

        f = (move >> 6) & 077
        fr = (f >> 3) & 0x7
        ff = f & 0x7
        t = move & 077
        tr = (t >> 3) & 0x7
        tf = t & 0x7
        p = (move >> 12) & 0x7
        pv = chr(ff + ord('a')) + chr(fr + ord('1')) + chr(tf + ord('a')) + chr(tr + ord('1'))
        if p:
            pv += " nbrq"[p]

        return {"e1h1": "e1g1", "e1a1": "e1c1", "e8h8": "e8g8", "e8a8": "e8c8"}.get(pv, pv)


class Polyglot:
    """
        fen = "rnbqkbnr/pppppppp/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        fich = "varied.bin"

        p = Polyglot()
        li = p.lista( fich, fen )

        for entry in li:
            p rint entry.pv(), entry.weight
    """

    random64 = (
        11329126462075137345L, 3096006490854172103L, 4961560858198160711L, 11247167491742853858L, 8467686926187236489L,
        3643601464190828991L,
        1133690081497064057L, 16733846313379782858L, 972344712846728208L, 1875810966947487789L, 10810281711139472304L,
        14997549008232787669L,
        4665150172008230450L, 77499164859392917L, 6752165915987794405L, 2566923340161161676L, 419294011261754017L,
        7466832458773678449L,
        8379435287740149003L, 9012210492721573360L, 9423624571218474956L, 17519441378370680940L, 3680699783482293222L,
        5454859592240567363L,
        12278110483549868284L, 10213487357180498955L, 9786892961111839255L, 1870057424550439649L, 13018552956850641599L,
        8864492181390654148L,
        14503047275519531101L, 2642043227856860416L, 5521189128215049287L, 1488034881489406017L, 12041389016824462739L,
        236592455471957263L,
        7168370738516443200L, 707553987122498196L, 3852097769995099451L, 8313129892476901923L, 1761594034649645067L,
        2291114854896829159L,
        15208840396761949525L, 13805854893277020740L, 11490038688513304612L, 5903053950100844597L, 6666107027411611898L,
        18228317886339920449L,
        3626425922614869470L, 10120929114188361845L, 13383691520091894759L, 9148094160140652064L, 1284939680052264319L,
        7307368198934274627L,
        5611679697977124792L, 10869036679776403037L, 4819485793530191663L, 7866624006794876513L, 4794093907474700625L,
        6849775302623042486L,
        4177248038373896072L, 10648116955499083915L, 7195685255425235832L, 17012007340428799350L, 6004979459829542343L,
        575228772519342402L,
        5806056339682094430L, 8920438500019044156L, 1872523786854905556L, 7168173152291242201L, 9388215746117386743L,
        8767779863385330152L,
        1489771135892281206L, 17385502867130851733L, 15762364259840250620L, 2649182342564336630L, 13505777571156529898L,
        928423270205194457L,
        11861585534482611396L, 16833723316851456313L, 2875176145464482879L, 9598842341590061041L, 6103491276194240627L,
        8264435384771931435L,
        17191732074717978439L, 11134495390804798113L, 8118948727165493749L, 17994305203349779906L, 9778408473133385649L,
        11774350857553791160L,
        12559012443159756018L, 1810658488341658557L, 9781539968129051369L, 658149708018956377L, 18376927623552767184L,
        10225665576382809422L,
        11247233359009848457L, 12966474917842991341L, 4111328737826509899L, 6628917895947053289L, 2166287019647928708L,
        11129710491401161907L,
        5728850993485642500L, 7135057069693417668L, 2409960466139986440L, 6600979542443030540L, 5794634036844991298L,
        1765885809474863574L,
        7278670237115156036L, 16128398739451409575L, 17262998572099182834L, 8877430296282562796L, 13401997949814268483L,
        407550088776850295L,
        13080877114316753525L, 5365205568318698487L, 14935709793025404810L, 17669982663530100772L, 4357691132969283455L,
        17142609481641189533L,
        8763584794241613617L, 9679198277270145676L, 10941274620888120179L, 11693142871022667058L, 306186389089741728L,
        10524424786855933342L,
        8136607301146677452L, 8332101422058904765L, 6215931344642484877L, 17270261617132277633L, 13484155073233549231L,
        5040091220514117480L,
        10596830237594186850L, 18403699292185779873L, 12565676100625672816L, 15937214097180383484L,
        9145986266726084057L, 2521545561146285852L,
        14490332804203256105L, 9262732965782291301L, 16052069408498386422L, 2012514900658959106L, 4851386166840481282L,
        12292183054157138810L,
        12139508679861857878L, 7319524202191393198L, 16056131139463546102L, 2445601317840807269L, 12976440137245871676L,
        10500241373960823632L,
        1211454228928495690L, 2931510483461322717L, 14252799396886324310L, 6217490319246239553L, 3253094721785420467L,
        11224557480718216148L,
        17235000084441506492L, 12619159779355142232L, 5189293263797206570L, 12606612515749494339L, 1850950425290819967L,
        5933835573330569280L,
        17649737671476307696L, 1240625309976189683L, 13611516503114563861L, 11359244008442730831L, 463713201815588887L,
        5603848033623546396L,
        5837679654670194627L, 13869467824702862516L, 13001586210446667388L, 12934789215927278727L, 2422944928445377056L,
        3310549754053175887L,
        8519766042450553085L, 17839818495653611168L, 15503797852889124145L, 16011257830124405835L, 862037678550916899L,
        3197637623672940211L,
        5210919022407409764L, 14971170165545012763L, 12708212522875260313L, 11160345150269715688L,
        11888460494489868490L, 16669255491632516726L,
        7618258446600650238L, 17993489941568846998L, 18188493901990876667L, 11270342415364539415L,
        10288892439142166224L, 7423022476929853822L,
        14215600671451202638L, 8710936142583354014L, 18346051800474256890L, 629718674134230549L, 10598630096540703438L,
        10666243034611769205L,
        16077181743459442704L, 4303848835390748061L, 15183795910155040575L, 17843919060799288312L,
        15561328988693261185L, 15662367820628426663L,
        3706272247737428199L, 12051713806767926385L, 11742603550742019509L, 5704473791139820979L, 9787307967224182873L,
        1637612482787097121L,
        8908762506463270222L, 17556853009980515212L, 4157033003383749538L, 18207866109112763428L, 1800584982121391508L,
        5477894166363593411L,
        4674885479076762381L, 10160025381792793281L, 7550910419722901151L, 8799727354050345442L, 11321311575067810671L,
        4039979115090434978L,
        3605513501649795505L, 3876110682321388426L, 12180869515786039217L, 8620494007958685373L, 5854220346205463345L,
        4855373848161890066L,
        15654983601351599195L, 5949110547793674363L, 5957016279979211145L, 11321480117988196211L, 8228060533160592200L,
        2094843038752308887L,
        8801329274201873314L, 297395810205168342L, 6489982145962516640L, 925952168551929496L, 6268205602454985292L,
        2903841526205938350L,
        359914117944187339L, 8371662176944962179L, 11139146693264846140L, 9807576242525944290L, 5795683315677088036L,
        12688959799593560697L,
        1070089889651807102L, 6778454470502372484L, 17760055623755082862L, 1983224895012736197L, 15760908081339863073L,
        942692161281275413L,
        12134286529149333529L, 10647676541963177979L, 11090026030168016689L, 5245566602671237210L, 9195060651485531055L,
        6368791473535302177L,
        3229483537647869491L, 15232282204279634326L, 928484295759785709L, 1909608352012281665L, 10412093924024305118L,
        5773445318897257735L,
        3990834569972524777L, 10771395766813261646L, 4209783265310087306L, 15318153364378526533L, 616435239304311520L,
        17961392050318287288L,
        7798983577523272147L, 3913469721920333102L, 15424667983992144418L, 6239239264182308800L, 1654244791516730287L,
        17228895932005785491L,
        6221161860315361832L, 17056602083001532789L, 13458912522609437003L, 12917665617485216338L, 7337288846716161725L,
        13022188282781700578L,
        12979943748599740071L, 510457344639386445L, 8796640079689568245L, 13565008864486958290L, 6465331256500611624L,
        11031297210088248644L,
        8017026739316632057L, 3627975979343775636L, 15052215649796371267L, 6222903725779446311L, 3527832623857636372L,
        15597050972685397327L,
        8924250025456295612L, 14400806714161458836L, 10699110515857614396L, 14468157413083537247L, 4223238849618215370L,
        15681850266533497060L,
        1140009269240963018L, 12966521765762216121L, 12695701950206930564L, 3881319844097050799L, 16858671235974049358L,
        17004178443650550617L,
        10544522896658866816L, 13378871666599081203L, 7580967567056532817L, 14279886347066493375L,
        14791316027199525482L, 13540141887354822347L,
        15889873206108611120L, 13441296750672675768L, 11798467976251859403L, 16858792058461978657L, 704784010218719535L,
        9596982322589424841L,
        9297677921824001878L, 687173692492309888L, 2573542046251205823L, 14064986013008197277L, 5122261027125484554L,
        12166444546397347981L,
        392580029432520891L, 13077660124902070727L, 16778702188287612735L, 3451078315256158032L, 1238907336018749328L,
        9205113463181886956L,
        1667962162104261376L, 10830753981784044039L, 4479827962372740717L, 13723669708721922220L, 17895945165757891767L,
        5275192813757817777L,
        2148246364622112874L, 2290795724393258885L, 18193581350273252090L, 1776293542351822525L, 14757011774120772237L,
        4313244667902787366L,
        12281515972708701602L, 16810874891151093887L, 13231770820477907822L, 15338037979535853741L,
        3321611548688927336L, 3305807524324674332L,
        13385011844708802686L, 7248312053715383136L, 10692263740491040132L, 15834887971838928217L,
        15164530629649278767L, 9112428691881135949L,
        7848957776938116907L, 10951816186743012388L, 8896660382367628050L, 9603906275513256852L, 8762207035762213579L,
        14987444343672838948L,
        9409751230138127831L, 10591026249259463665L, 7197363620976276483L, 14301381657157454364L, 6373588016705149671L,
        685071415365890925L,
        11485719029193745472L, 11525714121369126191L, 16463451990009075596L, 16713578179004591821L,
        6251124536988276734L, 6144308296388004591L,
        8880818733894805775L, 1303007271453773655L, 9174156641096830119L, 8824404812019774483L, 4420129794615782201L,
        9951556838786075828L,
        8883975763174874978L, 10736884308676275715L, 5595889224692918441L, 4306406647446967767L, 6704191827946442961L,
        9195534799547011879L,
        15724940538984617905L, 15915014237009546277L, 3928039610514994951L, 14873195079178728329L,
        12362539403674935092L, 4869881251581666789L,
        12986343614603388393L, 1215083005313393810L, 15835354158744478399L, 11186056805483324290L,
        13149236123055901828L, 13821214860367539280L,
        12182689304549523133L, 2305696533800337221L, 12399248800711438055L, 12612571074767202621L, 1949121388445288260L,
        13067734303660960050L,
        14085928898807657146L, 14099042149407050217L, 17561987301945706495L, 11512458344154956250L,
        7437568954088789707L, 7915171836405846582L,
        11752651295154297649L, 520574178807700830L, 9984063241072378277L, 16254155646211095029L, 8412807604418121470L,
        5609875541891257226L,
        11323858615586018348L, 8376971840073549054L, 1383314287233606303L, 15474222835752021056L, 5204145074798490767L,
        2167677454434536938L,
        10341418833443722943L, 8271005071015654673L, 15537457915439920220L, 10730891177390075310L,
        11511496483171570656L, 16026237624051288806L,
        11839117319019400126L, 11321351259605636133L, 5895970210948560438L, 3447475526873961356L, 7334775646005305872L,
        15954460007382865005L,
        6939292427400212706L, 8334626163711782046L, 1912937584935571784L, 12304971244567641760L, 8524679326357320614L,
        2204997376562282123L,
        3197166419597805379L, 4220875528993937793L, 2803169229572255230L, 5085503808422584221L, 14444799216525086860L,
        4570145336765972565L,
        9186432380899140933L, 11239615222781363662L, 9872907954749725788L, 10369691348610460342L, 11573842626212501214L,
        18049927275724560211L,
        15471783285232223897L, 16134745906572777443L, 13149419803421182712L, 14564139292183438565L,
        2088698177441502777L, 15099871677732932330L,
        5679318949880730421L, 16491038769688081874L, 1684901764271550206L, 6019498834983443029L, 8308552077872645018L,
        2774412133178445207L,
        2993471197969887147L, 8756104692490586069L, 7404378077533100169L, 11391825116471223489L, 17128408637045999621L,
        5816122712455824169L,
        5531291136777113635L, 7400684525794093602L, 2421696223438995901L, 2746718911238191773L, 2297623779240041360L,
        15514986454711725499L,
        13355177993350187464L, 2151598180055853022L, 14933732441462847914L, 17651243408385815107L, 4086544267540179726L,
        3960368502933186560L,
        16948614951473504462L, 11262612224635188739L, 12613511070148831882L, 2706199935239343179L,
        10054459213633325149L, 17640957734094436437L,
        15290986714861486531L, 16616573458614039565L, 2626432152093131908L, 14024745482209308341L,
        12344195406125417964L, 7167044992416702836L,
        11933989054878784040L, 1255659969011027721L, 3240842176865726111L, 795178308456769763L, 12389083385239203825L,
        6408553047871587981L,
        14331996049216472800L, 3362936192376505047L, 1486633608756523830L, 8937438391818961808L, 15513702763578092231L,
        9242607645174922067L,
        16999375738341892551L, 225631029947824688L, 5294122026845313316L, 11666909141406975304L, 6576914768872977647L,
        13014342141693467190L,
        15296769519938257969L, 1344590668019013826L, 8870296219354404L, 1763076921063072981L, 11710831831040350446L,
        11042296215092253456L,
        12923501896423220822L, 2679459049130362043L, 15149139477832742400L, 2006921612949215342L, 2441159149980359103L,
        4254066403785111886L,
        10165995291879048302L, 17968517685540419316L, 4067155115498534723L, 14584673823956990486L, 7262306400971602773L,
        2599246507224983677L,
        1183331494191622178L, 9203696637336472112L, 8684305384778066392L, 452576500022594089L, 7158260433795827572L,
        5749101480176103715L,
        2141838636388669305L, 13319697665469568251L, 11739738846189583585L, 15704600611932076809L,
        17288566729036156523L, 3345333136360207999L,
        12225668941959679643L, 13135848755558586049L, 8127707564878445808L, 11020438739076919854L,
        13800233257954351967L, 10719452353263111411L,
        4467639418469323241L, 13341252870622785523L, 7043015398453076736L, 13802777531561938248L, 2597087673064131360L,
        18196619797102886407L,
        17222554220133987378L, 11603572837337492490L, 9373650498706682568L, 15247985213323458255L, 2826050093225892884L,
        7047939442312345917L,
        1975862676241125979L, 8471065344236531211L, 10781433328192619353L, 12710259184248419661L, 6983092299355911633L,
        8891398163252015007L,
        18232837537224201402L, 10128874404256367960L, 1184291664448112016L, 8752186474456668498L, 11883874832968622155L,
        8304258407043758711L,
        13031437632736158055L, 11394657882570178521L, 11346359947151974253L, 15207539437603825135L,
        6743071165850287963L, 1895531807983368793L,
        8070015023023620019L, 15994912017468668362L, 7264555371116116147L, 638838107884199779L, 612060626599877907L,
        16368581545287660539L,
        2028126038944990910L, 8217932366665821866L, 12715716898990721499L, 4917760284400488853L, 4689038209317479950L,
        15570055495392019914L,
        7353589116749496814L, 6461588461223219363L, 16737230234434607639L, 10643751583066909176L, 13889371344374910415L,
        14623784806974468748L,
        6280119077769544053L, 5795026310427216669L, 15581542564775929183L, 5344020438314994897L, 17090582320435646615L,
        13070392342864893666L,
        2499216570383001617L, 5973851566933180981L, 11163195574208743088L, 10686881252049739702L, 7802414647854227001L,
        7696730671131205892L,
        11939552629336260711L, 8954801150602803298L, 5805966293032425995L, 10608482480047230587L, 4997389530575201269L,
        7710978612650642680L,
        7716832357345836839L, 15123312752564224361L, 16000314919358148208L, 5766400084981923062L, 11245886267645737076L,
        8713884558928322285L,
        7910921931260759656L, 17192478743862940141L, 3651028258442904531L, 4208705969817343911L, 3568641929344250749L,
        7493701010274154640L,
        2245920858524015772L, 13159017457951468389L, 12290633441485835508L, 17599068061438200851L,
        18107352842948477138L, 3841784002685309084L,
        3972025232192455038L, 7780701379940603769L, 14773200954226001784L, 16368109790951669962L, 11498059885876068682L,
        331717439817162336L,
        18209951341142539931L, 639100052003347099L, 10347169565922244001L, 13093097841025825382L, 2526013881820679475L,
        4894708394808468861L,
        4217798054095379555L, 2415982786774940751L, 2008219703699744969L, 6034935405124924712L, 16377935039880138091L,
        15469949637801139582L,
        6813989660423069229L, 3171782229498906237L, 12757488664123869734L, 4587441767303016857L, 1011542511767058351L,
        1218420902424652599L,
        11452069637570869555L, 15332250653395824223L, 9318912313336593440L, 10499356348280572422L,
        17042034373048666488L, 1805505087651779950L,
        13083730121955101027L, 9926866826056072641L, 12395083137174176754L, 13014086693993705056L,
        18092419734315653769L, 4496402702769466389L,
        4275128525646469625L, 16718947186147009622L, 2644524053331857687L, 16665345306739798209L, 756689505943647349L,
        6332958748006341455L,
        5397518675852254155L, 3282372277507744968L, 15124857616913606283L, 9958173582926173484L, 550475751710050266L,
        9535384695938759828L,
        11027794851313865315L, 1895999114042080393L, 17795970715748483584L, 3512907883609256988L, 10170876972722661254L,
        5100888107877796098L,
        14766188770308692257L, 5664728055166256274L, 1867780161745570575L, 5069314540135811628L, 10826357501146152497L,
        8428576418859462269L,
        6489498281288268568L, 248384571951887537L, 14408891171920865889L, 3830179243734057519L, 10976374785232997173L,
        12375273678367885408L,
        14917570089431431088L, 5317296011783481118L, 8812437177215009958L, 15702128452263965086L, 1418237564682130775L,
        8287918193617750527L,
        5641726496814939044L, 18399300296243087930L, 6176181444192939950L, 13286219625023629664L, 14609847597738937780L,
        15778618041730427743L,
        13113915167160321176L, 3534397173597697283L, 16753315048725296654L, 2378655170733740360L, 17894101054940110861L,
        551298419243755034L,
        14177640314441820846L, 18011171644070679608L, 1942137629605578202L, 17704970308598820532L,
        10820688583425137796L, 319261663834750185L,
        17320020179565189708L, 10828766552733203588L, 11254165892366229437L, 5921710089078452638L, 1692791583615940497L,
        3154220012138640370L,
        2462272376968205830L, 5215882904155809664L, 9063345109742779520L, 10012495044321978752L, 2282028593076952567L,
        16490284710305269338L,
        11358175869672944140L, 2648366387851958704L, 2535530668932196013L, 15386192992268326902L, 6797681746413993003L,
        9131737009282615627L,
        744965241806492274L, 15534171479957703942L, 11406512201534848823L, 1724859165393741376L, 2131804225590070214L,
        10649852818715990109L,
        7348272751505534329L, 15418610264624661717L, 14030296408486517359L, 6426639016335384064L, 14857241317133980380L,
        8982836549816060296L,
        2847738978322528776L, 14275200949057556108L, 1517491100508351526L, 11487065943069529588L, 7252270709068430025L,
        1454069630547688509L,
        879136823698237927L, 764541931096396549L, 16628452526739142958L, 8210570252116953863L, 17419012767447246106L,
        16656819168530874484L,
        10879562253146277412L, 9340840147615694245L, 6892625624787444041L, 6239858431661771035L, 10484131262376733793L,
        15135908441777759839L,
        3591372000141165328L, 17394508730963952016L, 11925077963498648480L, 2231224496660291273L, 8127998803539291684L,
        16292452481085749975L,
        16488107566197090L, 2060923303336906913L, 14929791059677233801L, 15052228947759922034L, 8630622898638529667L,
        7467898009369859339L,
        17930561480947107081L, 18287077397422080L,)

    randomPiece = random64
    randomCastle = random64[768:]
    randomEnPassant = random64[772:]
    randomTurn = random64[780:]

    piece_names = "pPnNbBrRqQkK"

    def hash(self, fen):

        board_s, to_move_c, castle_flags_s, ep_square_s, mp, jg = fen.split(" ")

        board = []
        for f in range(8):
            li = []
            board.append(li)
            for r in range(8):
                li.append("-")

        key = 0L

        r = 7
        f = 0
        p = 0
        lb = len(board_s)

        while p < lb:
            c = board_s[p]
            p += 1

            if c == '/':
                r -= 1
                f = 0

            elif '1' <= c <= '8':
                f += int(c)

            else:
                board[f][r] = c
                f += 1
        for f in range(8):
            for r in range(8):
                c = board[f][r]
                if c != '-':
                    p_enc = self.piece_names.index(c)
                    key ^= self.randomPiece[64 * p_enc + 8 * r + f]
        p = 0
        lb = len(castle_flags_s)

        while p < lb:
            c = castle_flags_s[p]
            p += 1

            if c == 'K':
                key ^= self.randomCastle[0]
            elif c == 'Q':
                key ^= self.randomCastle[1]
            elif c == 'k':
                key ^= self.randomCastle[2]
            elif c == 'q':
                key ^= self.randomCastle[3]

        if ep_square_s != '-':
            f = ord(ep_square_s[0]) - ord('a')
            if to_move_c == 'b':
                if (f > 0 and board[f - 1][3] == 'p') or (f < 7 and board[f + 1][3] == 'p'):
                    key ^= self.randomEnPassant[f]
            else:
                if (f > 0 and board[f - 1][4] == 'P') or (f < 7 and board[f + 1][4] == 'P'):
                    key ^= self.randomEnPassant[f]

        if to_move_c == 'w':
            key ^= self.randomTurn[0]

        return key

    def int_from_file(self, l, r):
        cad = self.f.read(l)

        if len(cad) != l:
            return True, 0
        for c in cad:
            r = (r << 8) + ord(c)
        return False, r

    def entry_from_file(self):

        entry = Entry()

        r = 0L
        ret, r = self.int_from_file(8, r)
        if ret:
            return True, None
        entry.key = r

        ret, r = self.int_from_file(2, r)
        if ret:
            return True, None
        entry.move = r & 0xFFFF

        ret, r = self.int_from_file(2, r)
        if ret:
            return True, None
        entry.weight = r & 0xFFFF

        ret, r = self.int_from_file(4, r)
        if ret:
            return True, None
        entry.learn = r & 0xFFFFFFFF

        return False, entry

    def find_key(self, key):

        first = -1
        try:
            if self.f.seek(-16, os.SEEK_END):
                entry = Entry()
                entry.key = key + 1
                return -1, entry
        except:
            return -1, None

        last = self.f.tell() / 16
        ret, last_entry = self.entry_from_file()
        while True:
            if last - first == 1:
                return last, last_entry

            middle = (first + last) / 2
            self.f.seek(16 * middle, os.SEEK_SET)
            ret, middle_entry = self.entry_from_file()
            if key <= middle_entry.key:
                last = middle
                last_entry = middle_entry
            else:
                first = middle

    def lista(self, fichero, fen):
        key = self.hash(fen)

        self.f = open(fichero, "rb")

        offset, entry = self.find_key(key)
        li = []
        if entry and entry.key == key:

            li.append(entry)

            self.f.seek(16 * (offset + 1), os.SEEK_SET)
            while True:
                ret, entry = self.entry_from_file()
                if ret or (entry.key != key):
                    break

                li.append(entry)

        self.f.close()
        del self.f

        return li

        # def listaJugadas( self, fen ):
        # li = self.lista( self.path, fen )
        # posicion = ControlPosicion.ControlPosicion()
        # posicion.leeFen( fen )

        # total = 0
        # maxim = 0
        # for entry in li:
        # w = entry.weight
        # total += w
        # if w > maxim:
        # maxim = w

        # listaJugadas = []
        # for entry in li:
        # pv = entry.pv()
        # w = entry.weight
        # pc = w*100.0/total if total else "?"
        # desde, hasta, coronacion = pv[:2], pv[2:4], pv[4:]
        # pgn = posicion.pgnSP( desde, hasta, coronacion )
        # listaJugadas.append( ( desde, hasta, coronacion, "%-5s -%7.02f%% -%7d"%( pgn, pc, w), 1.0*w/maxim ) )
        # return listaJugadas
