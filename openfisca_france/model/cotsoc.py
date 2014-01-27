# -*- coding:utf-8 -*-
#
# This file is part of OpenFisca.
# OpenFisca is a socio-fiscal microsimulation software
# Copyright © 2011 Clément Schaff, Mahdi Ben Jelloul
# Licensed under the terms of the GPL (version 3 or later) license
# (see openfisca/__init__.py for details)


from __future__ import division

import logging

from numpy import logical_not as not_, maximum as max_, minimum as min_, ones, zeros 

from openfisca_core.baremes import BaremeDict, combineBaremes, scaleBaremes
from openfisca_core.enumerations import Enum


CAT = Enum(['prive_non_cadre',
            'prive_cadre',
            'public_titulaire_etat',
            'public_titulaire_militaire',
            'public_titulaire_territoriale',
            'public_titulaire_hospitaliere',
            'public_non_titulaire'])

log = logging.getLogger(__name__)

# TODO: CHECK la csg déductible en 2006 est case GH
# TODO:  la revenus soumis aux csg déductible et imposable sont en CG et BH en 2010

#        # Heures supplémentaires exonérées
#        if not self.bareme.ir.autre.hsup_exo:
#            self.sal += self.hsup
#            self.hsup = 0*self.hsup

# Exonération de CSG et de CRDS sur les revenus du chômage
# et des préretraites si cela abaisse ces revenus sous le smic brut
# TODO: mettre un trigger pour l'éxonération des revenus du chômage sous un smic

# TODO: RAFP assiette + prime
# TODO: pension assiette = salaire hors prime
# autres salaires + primes


# TODO: contribution patronale de prévoyance complémentaire
# Formation professionnelle (entreprise de 10 à moins de 20 salariés) salaire total 1,05%
# Formation professionnelle (entreprise de moins de 10 salariés)      salaire total 0,55%
# Taxe sur les salaries (pour ceux non-assujettis à la TVA)           salaire total 4,25%
# TODO: accident du travail ?

#temp = 0
#if hasattr(P, "prelsoc"):
#    for val in P.prelsoc.__dict__.itervalues(): temp += val
#    P.prelsoc.total = temp
#else :
#    P.__dict__.update({"prelsoc": {"total": 0} })
#
#a = {'sal':sal, 'pat':pat, 'csg':csg, 'crds':crds, 'exo_fillon': P.cotsoc.exo_fillon, 'lps': P.lps, 'ir': P.ir, 'prelsoc': P.prelsoc}
#return Dicts2Object(**a)

from .. import DEBUG_COTSOC

DEBUG = DEBUG_COTSOC

def _mhsup(hsup):
    """
    Heures supplémentaires comptées négativement
    """
    return -hsup

############################################################################
## Revenus du capital
############################################################################

# revenus du capital soumis au barème
def _csg_cap_bar(rev_cap_bar, _P):
    '''
    Calcule la CSG sur les revenus du captial soumis au barème
    '''
    return - rev_cap_bar*_P.csg.capital.glob

def _crds_cap_bar(rev_cap_bar, _P):
    '''
    Calcule la CRDS sur les revenus du capital soumis au barème
    '''
    return - rev_cap_bar*_P.crds.capital

def _prelsoc_cap_bar(rev_cap_bar, _P):
    '''
    Calcule le prélèvement social sur les revenus du capital soumis au barème
    '''
#    if DEBUG:
#        return - rev_cap_bar*0
    P = _P.prelsoc
    if _P.datesim.year < 2006:
        total = P.base_pat
    elif _P.datesim.year < 2009:
        total = P.base_pat + P.add
    else:
        total = P.base_pat + P.add + P.rsa
    return - rev_cap_bar*total

# plus-values de valeurs mobilières

def _csg_pv_mo(f3vg, _P):
    """
    Calcule la CSG sur les plus-values de cession immobilière
    """
    return - f3vg*_P.csg.capital.glob


def _crds_pv_mo(f3vg, _P):
    """
    Calcule la CRDS sur les plus-values de cession immobilière
    """
    return - f3vg*_P.crds.capital

def _prelsoc_pv_mo(f3vg, _P):
    """
    Calcule le prélèvement social sur les plus-values de cession de valeurs mobilières
    """
    P = _P.prelsoc
    if _P.datesim.year < 2006:
        total = P.base_pat
    elif _P.datesim.year < 2009:
        total = P.base_pat + P.add
    else:
        total = P.base_pat + P.add + P.rsa
    return - f3vg*total


# plus-values immobilières

def _csg_pv_immo(f3vz, _P):
    """
    Calcule la CSG sur les plus-values de cession immobilière
    """
    return - f3vz*_P.csg.capital.glob


def _crds_pv_immo(f3vz, _P):
    """
    Calcule la CRDS sur les plus-values de cession immobilière
    """
    return - f3vz*_P.crds.capital

def _prelsoc_pv_immo(f3vz, _P):
    """
    Calcule le prélèvement social sur les plus-values de cession immobilière
    """
    P = _P.prelsoc
    if _P.datesim.year < 2006:
        total = P.base_pat
    elif _P.datesim.year < 2009:
        total = P.base_pat + P.add
    else:
        total = P.base_pat + P.add + P.rsa
    return - f3vz*total


# revenus fonciers
def _csg_fon(f4ba, _P):
    '''
    Calcule la CSG sur les revenus fonciers
    '''
    return - f4ba*_P.csg.capital.glob

def _crds_fon(f4ba, _P):
    '''
    Calcule la CRDS sur les revenus fonciers
    '''
    return - f4ba*_P.crds.capital

def _prelsoc_fon(f4ba, _P):
    '''
    Calcule le prélèvement social sur les revenus fonciers
    '''
    P = _P.prelsoc
    if _P.datesim.year < 2006:
        total = P.base_pat
    elif _P.datesim.year < 2009:
        total = P.base_pat + P.add
    else:
        total = P.base_pat + P.add + P.rsa
    return - f4ba*total

# revenus du capital soumis au prélèvement libératoire
def _csg_cap_lib(rev_cap_lib, _P):
    '''
    Calcule la CSG sur les revenus du capital soumis au prélèvement libératoire
    '''
    return - rev_cap_lib*_P.csg.capital.glob

def _crds_cap_lib(rev_cap_lib, _P):
    '''
    Calcule la CRDS sur les revenus du capital soumis au prélèvement libératoire
    '''
    return - rev_cap_lib*_P.crds.capital

def _prelsoc_cap_lib(rev_cap_lib, _P):
    '''
    Calcule le prélèvement social sur les revenus du capital soumis au prélèvement libératoire
    '''
#    if DEBUG:
#        return - rev_cap_lib*0
    P = _P.prelsoc
    if _P.datesim.year < 2006:
        total = P.base_pat
    elif _P.datesim.year < 2009:
        total = P.base_pat + P.add
    else:
        total = P.base_pat + P.add + P.rsa
    return - rev_cap_lib*total


# TODO: non_imposabilité pour les revenus au barème
#        verse = (-csgcap_bar - crdscap_bar - prelsoccap_bar) > bareme.csg.capital.nonimp
##        verse=1
#        # CSG sur les revenus du patrimoine non imposés au barême (contributions sociales déjà prélevées)
#
#        table.setIndiv('csgcap_bar', csgcap_bar*verse)
#        table.setIndiv('prelsoccap_bar', prelsoccap_bar*verse)
#        table.setIndiv('crdscap_bar', crdscap_bar*verse)


############################################################################
## Salaires
############################################################################

def _salbrut(sali, hsup, type_sal, _defaultP):
    '''
    Calcule le salaire brut à partir du salaire net
    '''
    plaf_ss = 12*_defaultP.cotsoc.gen.plaf_ss

    salarie = scaleBaremes(BaremeDict('sal', _defaultP.cotsoc.sal), plaf_ss)
    csg = scaleBaremes(BaremeDict('csg', _defaultP.csg), plaf_ss)

    salarie['noncadre'].update(salarie['commun'])
    salarie['cadre'].update(salarie['commun'])


    noncadre = combineBaremes(salarie['noncadre'])
    cadre    = combineBaremes(salarie['cadre'])
    fonc     = combineBaremes(salarie['fonc'])

    # On ajoute la CSG deductible
    noncadre.addBareme(csg['act']['deduc'])
    cadre.addBareme(csg['act']['deduc'])
    fonc.addBareme(csg['act']['deduc'])

    nca = noncadre.inverse()
    cad = cadre.inverse()
    fon = fonc.inverse()

    # TODO: complete this to deal with the fonctionnaire
    brut_nca = nca.calc(sali)
    brut_cad = cad.calc(sali)
    brut_fon = fon.calc(sali)

    salbrut = (brut_nca*(type_sal == CAT['prive_non_cadre']) +
               brut_cad*(type_sal == CAT['prive_cadre']) +
               brut_fon*(type_sal == CAT['public_titulaire_etat']) )
    
    #print " nombre de barème:", len(salarie['noncadre'])
    #for name, bar in salarie['noncadre'].iteritems():
    #    print bar

    return salbrut + hsup


def _type_sal(titc, statut, chpub, cadre, _P):
    '''
    Catégorie de salarié
    0: prive_non_cadre
    1: prive_cadre
    2: public_titulaire_etat
    3: public_titulaire_militaire
    4: public_titulaire_territoriale
    5: public_titulaire_hospitalière
    6: public_non_titulaire
    '''
    cadre    = (statut ==8)*(chpub>3)*cadre
    noncadre = (statut ==8)*(chpub>3)*not_(cadre)

    etat_stag = (chpub==1)*(titc == 1)
    etat_tit  = (chpub==1)*(titc == 2)
    etat_cont = (chpub==1)*(titc == 3)

    colloc_stag = (chpub==2)*(titc == 1)
    colloc_tit  = (chpub==2)*(titc == 2)
    colloc_cont = (chpub==2)*(titc == 3)

    hosp_stag = (chpub==2)*(titc == 1)
    hosp_tit  = (chpub==2)*(titc == 2)
    hosp_cont = (chpub==2)*(titc == 3)

    contract = (colloc_cont + hosp_cont + etat_cont) > 1
    return 0 + 1*cadre + 2*etat_tit + 4*colloc_tit + 5*hosp_tit + 6*contract
    

def _taille_entreprise(nbsala):
    '''
    0 : "Non pertinent"
    1 : "Moins de 10 salariés"
    2 : "De 10 à 19 salariés"
    3 : "De 20 à 249 salariés"
    4 : "Plus de 250 salariés"
    '''
    return 0 + 1*(nbsala>=1) + 1*(nbsala>=10) + 1*(nbsala>=20) + 1*(nbsala>=250)


def build_pat(_P):
    '''
    Construit le dictionnaire de barèmes des cotisations patronales
    à partir des informations contenues dans P.cotsoc.pat
    '''
    plaf_ss = 12*_P.cotsoc.gen.plaf_ss
    pat = scaleBaremes(BaremeDict('pat', _P.cotsoc.pat), plaf_ss)
    pat['noncadre'].update(pat['commun'])
    pat['cadre'].update(pat['commun'])
    pat['fonc']['contract'].update(pat['commun'])

    # Renaiming
    pat['prive_non_cadre'] =  pat.pop('noncadre')
    pat['prive_cadre'] =  pat.pop('cadre')

    log.info("Le dictionnaire des barèmes des cotisations patronales des non cadres contient %s", pat['prive_non_cadre'].keys())
    log.info("Le dictionnaire des barèmes des cotisations patronales des cadres contient %s", pat['prive_cadre'].keys())

    # Rework commun to deal with public employees
    for var in ["maladie", "apprentissage", "apprentissage2", "vieillesseplaf", "vieillessedeplaf", "formprof", "chomfg", "construction","assedic", "transport"]:
        del pat['commun'][var]

    for var in ["apprentissage", "apprentissage2", "formprof", "chomfg", "construction","assedic"]:
        del pat['fonc']['contract'][var]

    pat['fonc']['etat'].update(pat['commun'])
    pat['fonc']['colloc'].update(pat['commun'])
    del pat['commun']

    pat['etat_t'] = pat['fonc']['etat']
    pat['colloc_t'] = pat['fonc']['colloc']
    pat['contract'] =  pat['fonc']['contract']
    
    for var in ['etat', 'colloc', 'contract' ]:
        del pat['fonc'][var]
        
    # Renaiming
    pat['public_titulaire_etat'] =  pat.pop('etat_t')
    pat['public_titulaire_territoriale'] =  pat.pop('colloc_t')
#    pat['public_titulaire_hospitalière'] =  pat.pop('colloc') TODO: fix ths
    pat['public_non_titulaire'] =  pat.pop('contract')
        
    log.info("Le dictionnaire des barèmes des cotisations patronales des salariés titulaires de l'etat contient %s", pat['public_titulaire_etat'].keys())
    log.info("Le dictionnaire des barèmes des cotisations patronales titulaires des collectivités locales contient %s", pat['public_titulaire_territoriale'].keys())
    log.info("Le dictionnaire des barèmes des cotisations patronales du public contractuels contient %s", pat['public_non_titulaire'].keys())
    
    return pat


def _cotpat_contrib(salbrut, hsup, type_sal, _P):
    '''
    Cotisation sociales patronales contributives
    '''
    pat = build_pat(_P)
    cotpat = zeros(len(salbrut))
    for category in CAT:
        iscat = (type_sal == category[1]) # category[1] is the numerical index
        if category[0] in pat.keys():
            for bar in pat[category[0]].itervalues():
                is_contrib = (bar.option == "contrib")
                temp = - (iscat*bar.calc(salbrut))*is_contrib
                cotpat += temp
                #if is_contrib == 1: 
                #    log.info(bar)
                #    log.info(temp)
    return cotpat

def _cotpat_main_d_oeuvre(salbrut, hsup, type_sal, _P):
    '''
    Cotisation sociales patronales main d'oeuvre (TODO: complete avec justiofactiuon TaxIPP)
    '''
    pat = build_pat(_P)
    cotpat = zeros(len(salbrut))
    for category in CAT:
        iscat = (type_sal == category[1]) # category[1] is the numerical index
        if category[0] in pat.keys():
            for bar in pat[category[0]].itervalues():
                is_mo = (bar.option == "main_d_oeuvre")
                temp = - (iscat*bar.calc(salbrut))*is_mo
                cotpat += temp
                #if is_mo == 1: 
                #    log.info(bar)
                #    log.info(temp)
    return cotpat

def _cotpat_transport(salbrut, hsup, type_sal, _P):
    '''
    Versement transport
    '''
    pat = build_pat(_P)
    transport = zeros(len(salbrut))
    for category in CAT:
        iscat = (type_sal == category[1]) # category[1] is the numerical index of the category
        if category[0] in pat.keys():     # category[0] is the name of the category
            if 'transport' in pat[category[0]]:
                bar = pat[category[0]]['transport']
                temp = - bar.calc(salbrut)*iscat
                transport += temp
                #log.info(bar)
                #log.info(transport)
    return transport

def _cotpat_accident(salbrut, taux_accident_travail):  # taux_accident_travail
    '''
    Cotisations patronales accident du travail et maladie professionelle
    '''
    return -salbrut*taux_accident_travail
    
    
def _cotpat_noncontrib(salbrut, hsup, type_sal, cotpat_accident, _P):
    '''
    Cotisation sociales patronales non contributives
    '''
    pat = build_pat(_P)
    cotpat = zeros(len(salbrut))
    for category in CAT:
        iscat = (type_sal == category[1])
        if category[0] in pat.keys():
            for bar in pat[category[0]].itervalues():
                is_noncontrib = (bar.option == "noncontrib")
                temp = - (iscat*bar.calc(salbrut))*is_noncontrib
                cotpat += temp
                if is_noncontrib == 1: 
                    log.info(bar)
                    log.info(temp)
    return cotpat + cotpat_accident

def _cotpat(cotpat_contrib, cotpat_noncontrib, cotpat_main_d_oeuvre, cotpat_transport):
    '''
    Cotisations sociales patronales
    '''
    return cotpat_contrib + cotpat_noncontrib + cotpat_main_d_oeuvre + cotpat_transport


def build_sal(_P):
    '''
    Construit le dictionnaire de barèmes des cotisations salariales
    à partir des informations contenues dans P.cotsoc.sal
    '''
    plaf_ss = 12*_P.cotsoc.gen.plaf_ss

    sal = scaleBaremes(BaremeDict('sal', _P.cotsoc.sal), plaf_ss)
    sal['noncadre'].update(sal['commun'])
    sal['cadre'].update(sal['commun'])
    
    # Renaiming
    sal['prive_non_cadre'] =  sal.pop('noncadre')
    sal['prive_cadre'] =  sal.pop('cadre')
    
    sal['etat_t'] = sal['fonc']['etat']
    sal['colloc_t'] = sal['fonc']['colloc']
    sal['contract'] = sal['fonc']['contract']

    sal['contract'].update(sal['commun'])
    del sal['contract']['arrco']
    del sal['contract']['assedic']
    sal['contract']['solidarite'] = sal['fonc']['commun']['solidarite']

    del sal['fonc']['etat']
    del sal['fonc']['colloc']
    del sal['fonc']['contract']
    del sal['commun']

    # Renaiming
    sal['public_titulaire_etat'] =  sal.pop('etat_t')
    sal['public_titulaire_territoriale'] =  sal.pop('colloc_t')
#    pat['public_titulaire_hospitalière'] =  pat.pop('colloc') TODO: fix ths
    sal['public_non_titulaire'] =  sal.pop('contract')
    
    log.info("Le dictionnaire des barèmes des salariés titualires de l'etat contient %s", sal['public_titulaire_etat'].keys())
    log.info("Le dictionnaire des barèmes des salariés titualires des collectivités locales contient %s", sal['public_titulaire_territoriale'].keys())
    log.info("Le dictionnaire des barèmes des salariés du public contractuels contient %s", sal['public_non_titulaire'].keys())
    return sal


def seuil_fds(_P):
    '''
    Calcul du seuil mensuel d'assujetissement à la contribution au fond de solidarité
    '''
    from math import  floor
    ind_maj_ref = _P.cotsoc.sal.fonc.commun.ind_maj_ref
    pt_ind = _P.cotsoc.sal.fonc.commun.pt_ind
    seuil_mensuel = floor(100*(pt_ind*ind_maj_ref)/12)
    return seuil_mensuel

def _cotsal_contrib(salbrut, hsup, type_sal, _P):
    '''
    Cotisations sociales salariales contributives
    '''
    sal = build_sal(_P)
    cotsal = zeros(len(salbrut))
    for category in CAT:
        iscat = (type_sal == category[1])
        if category[0] in sal:
            for bar in sal[category[0]].itervalues():
                is_contrib = (bar.option == "contrib")
                temp = - (iscat*bar.calc(salbrut-hsup))*is_contrib
                cotsal += temp    
    return cotsal



def _cotsal_noncontrib(salbrut, hsup, type_sal, _P):
    '''
    Cotisations sociales salariales non-contributives
    '''
    sal = build_sal(_P)
    cotsal = zeros(len(salbrut))
    seuil_assuj_fds = seuil_fds(_P)
    for category in CAT:
        iscat = (type_sal == category[1])
        if category[0] in sal:
            for bar in sal[category[0]].itervalues():
                is_noncontrib = (bar.option == "noncontrib")
                is_exempt_fds = (category[0] in ['public_titulaire_etat', 'public_titulaire_territoriale'])*(bar._name == 'solidarite')*( (salbrut-hsup) <= seuil_assuj_fds)   #TODO: check assiette voir IPP
                if DEBUG:
                    is_noncontrib = ( (bar.option == "noncontrib") and (bar._name in ["famille", "maladie"] ))
                temp = - (iscat*bar.calc(salbrut-hsup))*is_noncontrib*not_(is_exempt_fds)
                cotsal += temp
    return cotsal

def _cotsal(cotsal_contrib, cotsal_noncontrib):
    '''
    Cotisations sociales salariales
    '''
    return cotsal_contrib + cotsal_noncontrib


def _csgsald(salbrut, hsup, _P):
    '''
    CSG deductible sur les salaires
    '''
    plaf_ss = 12*_P.cotsoc.gen.plaf_ss
    csg = scaleBaremes(_P.csg.act.deduc, plaf_ss)
    return - csg.calc(salbrut - hsup)


def _csgsali(salbrut, hsup, _P):
    '''
    CSG imposable sur les salaires
    '''
    plaf_ss = 12*_P.cotsoc.gen.plaf_ss
    csg = scaleBaremes(_P.csg.act.impos, plaf_ss)
    return  - csg.calc(salbrut - hsup)


def _crdssal(salbrut, hsup, _P):
    '''
    CRDS sur les salaires
    '''
    plaf_ss = 12*_P.cotsoc.gen.plaf_ss
    crds = scaleBaremes(_P.crds.act, plaf_ss)
    return - crds.calc(salbrut - hsup)


def _sal_h_b(salbrut):
    '''
    Salaire horaire brut
    '''
    nbh_travaillees = 151.67*12
    return salbrut/nbh_travaillees


def _alleg_fillon(salbrut, sal_h_b, type_sal, _P):
    '''
    Allègement de charges patronales sur les bas et moyens salaires
    dit allègement Fillon
    '''
    P = _P.cotsoc
    taux_fillon = taux_exo_fillon(sal_h_b, P)
    alleg_fillon = taux_fillon*salbrut*(type_sal == CAT['prive_non_cadre'])
    return alleg_fillon

def _sal(salbrut, csgsald, cotsal, hsup):
    '''
    Calcul du salaire imposable
    '''
    return salbrut + csgsald + cotsal - hsup


def _salsuperbrut(salbrut, cotpat, alleg_fillon):
    return salbrut - cotpat - alleg_fillon


############################################################################
## Allocations chômage
############################################################################

def exo_csg_chom(choi, _P):
    '''
    Indicatrice d'exonération de la CSG sur les revenus du chômage
    '''
    # TODO: on néglige la csg imposable ...
    nbh_travail = 151.67 # depuis 2001
    cho_seuil_exo = _P.csg.chom.min_exo*nbh_travail*_P.cotsoc.gen.smic_h_b
    return (choi <= 12*cho_seuil_exo) # annuel


def _csg_rempl(rfr_n_2, nbpt_n_2, chobrut, rstbrut, _P):
    '''
    Taux retenu sur la CSG des revenus de remplacment:
    0 : Non renseigné/non pertinent
    1 : Exonéré
    2 : Taux réduit
    3 : Taux plein
    '''
    # TODO: problème avec le rfr n-2
    P = _P.cotsoc.gen
    seuil_th = P.plaf_th_1 + P.plaf_th_supp*(max_(0, (nbpt_n_2-1)/2))
    res =  (0 +
            max_((chobrut>0) + (rstbrut>0), 0) +
            (rfr_n_2 >= seuil_th) +
            1  ) # conditon sur impot avant credit > seuil de non imposition
    return 3*ones(len(res))

    
def _chobrut(choi, csg_rempl, _defaultP):
    '''
    Calcule les allocations chômage brute à partir des allocations imposables
    '''
    # TODO: ajouter la crds ?
    P = _defaultP.csg.chom
    plaf_ss = 12*_defaultP.cotsoc.gen.plaf_ss
    csg = scaleBaremes(BaremeDict('csg', P), plaf_ss)
    taux_plein = csg['plein']['deduc']
    taux_reduit = csg['reduit']['deduc']
    
    log.info(taux_plein)
    log.info(taux_reduit)
    
    chom_plein = taux_plein.inverse()
    chom_reduit = taux_reduit.inverse()
    log.info(chom_plein)
    log.info(chom_reduit)
    chobrut = (csg_rempl==1)*choi + (csg_rempl==2)*chom_reduit.calc(choi) + (csg_rempl==3)*chom_plein.calc(choi)
    #isexo = exo_csg_chom(choi, _defaultP)
    #chobrut = not_(isexo)*chobrut + (isexo)*choi
#     print  P.plein.impos,  P.plein.deduc
#     print "taux réduit : "
#     print  P.reduit.impos,  P.reduit.deduc
    return chobrut


def _csgchod(chobrut, csg_rempl, _P):
    '''
    CSG déductible sur les allocations chômage
    '''
    plaf_ss = 12*_P.cotsoc.gen.plaf_ss
    csg = scaleBaremes(BaremeDict('csg', _P.csg.chom), plaf_ss)
    taux_plein = csg['plein']['deduc'].calc(chobrut)
    taux_reduit = csg['reduit']['deduc'].calc(chobrut)
    csgchod = (csg_rempl==2)*taux_reduit + (csg_rempl==3)*taux_plein
    #isexo = exo_csg_chom(chobrut, _P)
    # return - not_(isexo)*csgchod
    return - csgchod

def _csgchoi(chobrut, csg_rempl, _P):
    '''
    CSG imposable sur les allocations chômage
    '''
    plaf_ss = 12*_P.cotsoc.gen.plaf_ss
    csg = scaleBaremes(BaremeDict('csg', _P.csg.chom), plaf_ss)
    taux_plein = csg['plein']['impos'].calc(chobrut)
    taux_reduit = csg['reduit']['impos'].calc(chobrut)
    csgchoi = (csg_rempl==2)*taux_reduit + (csg_rempl==3)*taux_plein
    #isexo = exo_csg_chom(chobrut, _P)
    #return - not_(isexo)*csgchoi
    return -csgchoi

def _crdscho(chobrut, _P):
    '''
    CRDS sur les allocations chômage
    '''
    plaf_ss = 12*_P.cotsoc.gen.plaf_ss
    crds = scaleBaremes(_P.crds.act, plaf_ss)
    return - crds.calc(chobrut)

def _cho(chobrut, csgchod, _P):
    '''
    Chômage imposable (recalculé)
    '''
#     isexo = exo_csg_chom(chobrut, _P)  # TODO: check
    return chobrut + csgchod #+ not_(isexo)*csgchod

def _chonet(cho, csgchoi, crdscho):
    '''
    Chômage net
    '''
    return cho + csgchoi + crdscho

############################################################################
## Pensions
############################################################################
def _rstbrut(rsti, csg_rempl, _defaultP):
    '''
    Calcule les pensions de retraites brutes à partir des pensions imposables
    '''
    P = _defaultP.csg.retraite
    rst_plein = P.plein.deduc.inverse()  # TODO:     rajouter la non  déductible dans param
    rst_reduit = P.reduit.deduc.inverse()  #
    rstbrut = (csg_rempl==2)*rst_reduit.calc(rsti) + (csg_rempl==3)*rst_plein.calc(rsti)
    return rstbrut

def _csgrstd(rstbrut, csg_rempl, _P):
    '''
    CSG déductible sur les allocations chômage
    '''
    plaf_ss = 12*_P.cotsoc.gen.plaf_ss
    csg = scaleBaremes(BaremeDict('csg', _P.csg.retraite), plaf_ss)
    taux_plein = csg['plein']['deduc'].calc(rstbrut)
    taux_reduit = csg['reduit']['deduc'].calc(rstbrut)
    csgrstd = (csg_rempl==3)*taux_plein + (csg_rempl==2)*taux_reduit
    return - csgrstd

def _csgrsti(rstbrut, csg_rempl, _P):
    '''
    CSG imposable sur les pensions de retraite
    '''
    plaf_ss = 12*_P.cotsoc.gen.plaf_ss
    csg = scaleBaremes(BaremeDict('csg', _P.csg.retraite), plaf_ss)
    taux_plein = csg['plein']['impos'].calc(rstbrut)
    taux_reduit = csg['reduit']['impos'].calc(rstbrut)
    csgrsti = (csg_rempl==3)*taux_plein + (csg_rempl==2)*taux_reduit
    return - csgrsti

def _crdsrst(rstbrut, _P):
    '''
    CRDS sur les pensions
    '''
    plaf_ss = 12*_P.cotsoc.gen.plaf_ss
    crds = scaleBaremes(BaremeDict('crds', _P.crds.rst), plaf_ss)
    return - crds['rst'].calc(rstbrut)

def _rst(rstbrut, csgrstd):
    '''
    Calcule les pensions imposables
    '''
    return rstbrut + csgrstd

def _rstnet(rst, csgrsti, crdsrst):
    '''
    Retraites nettes
    '''
    return rst + csgrsti + crdsrst

############################################################################
## Impôt Landais, Piketty, Saez
############################################################################

def _base_csg(salbrut, chobrut, rstbrut, rev_cap_bar, rev_cap_lib):
    '''
    Assiette de la csg
    '''
    return salbrut + chobrut + rstbrut + rev_cap_bar + rev_cap_lib

def _ir_lps(base_csg, nbF, nbH, statmarit, _P ):
    '''
    Impôt individuel sur l'ensemble de l'assiette de la csg, comme proposé par
    Landais, Piketty, Saez (2011)
    '''
    P = _P.lps
    nbEnf = (nbF + nbH/2)
    ae = nbEnf*P.abatt_enfant
    re = nbEnf*P.reduc_enfant
    ce = nbEnf*P.credit_enfant

    couple = (statmarit == 1) | (statmarit == 5)
    ac = couple*P.abatt_conj
    rc = couple*P.reduc_conj

    return - max_(0, P.bareme.calc(max_(base_csg - ae - ac, 0) )-re-rc) + ce


############################################################################
## Helper functions
############################################################################

def taux_exo_fillon(sal_h_b, P):
    '''
    Exonération Fillon
    http://www.securite-sociale.fr/comprendre/dossiers/exocotisations/exoenvigueur/fillon.htm
    '''
    # TODO Ainsi, à compter du 1er juillet 2007, le taux d’exonération des employeurs de 19 salariés au plus
    # passera pour une rémunération horaire égale au SMIC de 26 % à 28,1 %.

    # TODO la divison par zéro engendre un warning
    # Le montant maximum de l’allègement dépend de l’effectif de l’entreprise.
    # Le montant est calculé chaque année civile, pour chaque salarié ;
    # il est égal au produit de la totalité de la rémunération annuelle telle que visée à l’article L. 242-1 du code de la Sécurité sociale par un coefficient.
    # Ce montant est majoré de 10 % pour les entreprises de travail temporaire au titre des salariés temporaires pour lesquels elle est tenue à l’obligation
    # d’indemnisation compensatrice de congés payés.
    smic_h_b = P.gen.smic_h_b
    seuil = P.exo_fillon.seuil
    tx_max = P.exo_fillon.tx_max
    if seuil <= 1:
        return 0
    return tx_max*min_(1,max_(seuil*smic_h_b/(sal_h_b + 1e-10)-1,0)/(seuil-1))

