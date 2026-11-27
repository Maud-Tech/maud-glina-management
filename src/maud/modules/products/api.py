"""Fachada pública do módulo products: a ÚNICA coisa que outros módulos podem importar daqui.

Vazia até outro módulo precisar de produtos (ex.: fechamentos por apólice). A leitura pelo
app de passivo será pela API de leitura (task separada), não por esta fachada.
Mudar uma assinatura deste arquivo é mudança de contrato entre frentes: combine antes.
"""
