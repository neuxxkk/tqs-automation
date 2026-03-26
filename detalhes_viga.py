from TQS import TQSBuild, TQSExec

def processar_todas_vigas():
    nprjpv, nprjed, nombde, nomedi, nompav, istat = TQSBuild.BuildingContext()

    if istat != 0:
        print("Erro: Este script deve ser executado de dentro da pasta de um edifício TQS.")
        return

    print(f"Edifício identificado: {nomedi}")
    print("Preparando fila de processamento das vigas...")

    job = TQSExec.Job()

    tarefa_pasta = TQSExec.TaskFolder(nomedi, TQSExec.TaskFolder.FOLDER_FRAMES)
    job.EnterTask(tarefa_pasta)

    # Configura a tarefa de Processamento Global APENAS para detalhar e extrair relatórios
    tarefa_vigas = TQSExec.TaskGlobalProc(
        floorPlan=0, floorDraw=0, slabs=0, 
        
        beams=2,          # <--- ALTERADO DE 3 PARA 2 (Gera o RELGER e pula o desenho)
        
        columnsData=0, columns=0, columnsReport=0, 
        gridModel=0, gridDraw=0, gridExtr=0, gridAnalysis=0, 
        gridBeamsTrnsf=0, gridSlabsTrnsf=0, gridNonLinear=0, 
        frameModel=0, frameAnalysis=0, frameBeamsTrnsf=0, 
        frameColumnsTrnsf=0, foundations=0, stairs=0, 
        fire=0, precastPhases=0
    )
    
    job.EnterTask(tarefa_vigas)

    print("Iniciando o dimensionamento, detalhamento e desenho de todas as vigas...")
    job.Execute()
    
    print("Processamento de vigas concluído com sucesso!")

if __name__ == "__main__":
    processar_todas_vigas()
