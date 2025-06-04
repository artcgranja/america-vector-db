from enum import Enum
from typing import List, Union
from pydantic import BaseModel, Field

class EnergySubjectEnum(Enum):
    """
    Enumeração dos assuntos predefinidos para classificação de documentos do mercado de energia.
    """
    AUTOPRODUCAO = "Autoprodução"
    TARIFAS = "Tarifas"
    CONSUMO_ENERGIA = "Consumo de Energia"
    GERACAO_DISTRIBUIDA = "Geração Distribuída"
    ENERGIA_HIDROELETRICA = "Energia Hidroelétrica"
    ENERGIA_EOLICA = "Energia Eólica"
    ENERGIA_SOLAR_FOTOVOLTAICA = "Energia Solar Fotovoltaica"
    ENERGIA_SOLAR_TERMICA = "Energia Solar Térmica (Heliotérmica)"
    ENERGIA_NUCLEAR = "Energia Nuclear"
    ENERGIA_GEOTERMICA = "Energia Geotérmica"
    ENERGIA_BIOMASSA = "Energia de Biomassa"
    ENERGIA_FOSSIL_CARVAO = "Geração a Carvão Mineral"
    ENERGIA_FOSSIL_GAS_NATURAL = "Geração a Gás Natural"
    ENERGIA_FOSSIL_OLEO = "Geração a Óleo Combustível"
    COMERCIALIZACAO_ENERGIA = "Comercialização de Energia"
    REGULACAO_SETOR_ELETRICO = "Regulação do Setor Elétrico"
    EFICIENCIA_ENERGETICA = "Eficiência Energética"
    TRANSMISSAO_ENERGIA = "Transmissão de Energia"
    DISTRIBUICAO_ENERGIA = "Distribuição de Energia"
    MERCADO_LIVRE_ENERGIA = "Mercado Livre de Energia (ACL)"
    MERCADO_CATIVO_ENERGIA = "Mercado Regulado de Energia (ACR)"
    LEILOES_ENERGIA = "Leilões de Energia"
    PLANEJAMENTO_ENERGETICO = "Planejamento Energético"
    FINANCIAMENTO_PROJETOS_ENERGIA = "Financiamento de Projetos de Energia"
    MEIO_AMBIENTE_E_SUSTENTABILIDADE = "Meio Ambiente e Sustentabilidade (Setor Energético)"
    INOVACAO_E_TECNOLOGIA = "Inovação e Tecnologia (Setor Energético)"
    ARMAZENAMENTO_ENERGIA = "Armazenamento de Energia"
    HIDROGENIO_VERDE = "Hidrogênio Verde"
    CREDITOS_CARBONO_ENERGIA = "Créditos de Carbono (Setor Energético)"
    MOBILIDADE_ELETRICA = "Mobilidade Elétrica"

class ClassifierResponse(BaseModel):
    subjects: List[Union[EnergySubjectEnum, str]] = Field(
        ..., 
        description="Lista de assuntos do documento"
    )
    
    class Config:
        use_enum_values = True