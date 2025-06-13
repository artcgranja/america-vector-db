from src.app.db.models import SubjectModel
from src.app.db.session import get_db_session

# Temas do mercado de energia brasileiro
SUBJECTS = [
    # Geração e Fontes
    {"name": "Geração de Energia", "description": "Assuntos relacionados à produção de energia elétrica."},
    {"name": "Autoprodução", "description": "Geração de energia para consumo próprio."},
    {"name": "Geração Distribuída", "description": "Geração próxima ao consumo, incluindo micro e minigeração."},
    {"name": "Fontes Renováveis", "description": "Energia solar, eólica, biomassa, PCHs e outras fontes renováveis."},
    {"name": "Fontes Não Renováveis", "description": "Termelétricas, hidrelétricas e outras fontes convencionais."},
    
    # Transmissão e Distribuição
    {"name": "Transmissão de Energia", "description": "Assuntos sobre o transporte de energia elétrica em alta tensão."},
    {"name": "Transmissão Distribuidora", "description": "Ativos de transmissão operados por distribuidoras."},
    {"name": "Distribuição de Energia", "description": "Assuntos sobre a entrega de energia elétrica ao consumidor final."},
    
    # Mercado e Comercialização
    {"name": "Mercado Livre", "description": "Ambiente de contratação livre de energia elétrica."},
    {"name": "Mercado Cativo", "description": "Ambiente de contratação regulada de energia elétrica."},
    {"name": "Comercialização de Energia", "description": "Mercado livre, contratos e comercialização de energia."},
    {"name": "Migração de Consumidores", "description": "Processos de migração entre mercado cativo e livre."},
    
    # Contratos e Instrumentos Financeiros
    {"name": "Contratos de Energia", "description": "Tipos de contratos: convencionais, flexíveis, por disponibilidade e por quantidade."},
    {"name": "CCEAR", "description": "Contratos de Comercialização de Energia no Ambiente Regulado."},
    {"name": "Lastro e Energia", "description": "Conceitos de lastro para venda e energia contratada."},
    {"name": "Garantias Financeiras", "description": "Garantias exigidas para participação no mercado livre."},
    {"name": "Modulação", "description": "Flexibilização de contratos e modulação de energia."},
    {"name": "Back-to-Back", "description": "Operações de repasse de contratos entre agentes."},
    
    # Agentes e Modalidades
    {"name": "Agentes do Mercado", "description": "Comercializadores, PIE, autoprodutores e consumidores livres."},
    {"name": "Consumidores Especiais", "description": "Consumidores atendidos por fontes renováveis com regras específicas."},
    {"name": "Pools de Energia", "description": "Agrupamento de consumidores para compra conjunta."},
    {"name": "Portabilidade", "description": "Direitos de portabilidade do consumidor no mercado livre."},
    
    # Operação e Liquidação
    {"name": "PLD - Preço de Liquidação das Diferenças", "description": "Formação e aplicação do PLD no mercado de curto prazo."},
    {"name": "Sazonalização", "description": "Adequação dos montantes contratuais ao perfil de consumo."},
    {"name": "Liquidação CCEE", "description": "Processos de contabilização e liquidação financeira."},
    
    # Tarifas e Custos
    {"name": "Tarifas e Preços", "description": "Formação de tarifas, reajustes e políticas de preços."},
    {"name": "Tarifa de Sustentabilidade", "description": "Custos relacionados à sustentabilidade do setor elétrico."},
    {"name": "CDE - Conta de Desenvolvimento Energético", "description": "Subsídios e custos de desenvolvimento do setor."},
    {"name": "PIS/COFINS", "description": "Contribuições sociais sobre o setor elétrico."},
    
    # Regulação e Legislação
    {"name": "Regulação e Legislação", "description": "Normas, leis e regulamentações do setor elétrico."},
    {"name": "ANEEL", "description": "Agência Nacional de Energia Elétrica e suas resoluções."},
    {"name": "CCEE", "description": "Câmara de Comercialização de Energia Elétrica e suas regras."},
    {"name": "ONS", "description": "Operador Nacional do Sistema Elétrico e suas diretrizes."},
    
    # Eficiência e Sustentabilidade
    {"name": "Eficiência Energética", "description": "Uso racional e eficiente da energia."},
    {"name": "Mercado de Carbono", "description": "Créditos de carbono e sustentabilidade no setor energético."},
    {"name": "PEE - Programa de Eficiência Energética", "description": "Programas de eficiência energética regulados."},
    
    # Planejamento e Operação
    {"name": "Planejamento Energético", "description": "Estudos, projeções e planejamento do setor."},
    {"name": "Operação do Sistema", "description": "Operação, despacho e segurança do sistema elétrico."},
    {"name": "PDD - Procedimentos de Distribuição", "description": "Procedimentos técnicos de distribuição."},
    {"name": "PRODIST", "description": "Procedimentos de Distribuição de Energia Elétrica."},
    
    # Inovação e Tecnologia
    {"name": "Inovação e Tecnologia", "description": "Novas tecnologias, digitalização e modernização do setor."},
    {"name": "Smart Grid", "description": "Redes inteligentes e modernização da infraestrutura."},
    {"name": "Medição Inteligente", "description": "Sistemas de medição avançada e telemetria."},
    
    # Políticas e Consumidores
    {"name": "Política Energética", "description": "Diretrizes e políticas públicas para o setor de energia."},
    {"name": "Consumidor de Energia", "description": "Direitos, deveres e perfil do consumidor de energia."},
    {"name": "Subsídios Cruzados", "description": "Mecanismos de subsídios entre diferentes classes de consumidores."},
]

def main():
    session = next(get_db_session())
    try:
        subjects_added = 0
        for subject in SUBJECTS:
            exists = session.query(SubjectModel).filter_by(name=subject["name"]).first()
            if not exists:
                s = SubjectModel(name=subject["name"], description=subject["description"])
                session.add(s)
                subjects_added += 1
        
        session.commit()
        print(f"Seed realizado com sucesso!")
        print(f"Total de assuntos na lista: {len(SUBJECTS)}")
        print(f"Novos assuntos adicionados: {subjects_added}")
        print(f"Assuntos já existentes: {len(SUBJECTS) - subjects_added}")
        
    except Exception as e:
        session.rollback()
        print(f"Erro durante o seed: {e}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    main()