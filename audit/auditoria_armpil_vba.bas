Option Explicit

' ================================================================
' AUDITORIA ARMPIL vs SELE
' 1. Carregar ARMPIL.CSV
' 2. Carregar SELE.LST
' 3. Executar comparacao
'
' REGRAS:
' - As Total no ARMPIL fica como FORMULA:
'   As = Qtd * PI * Bitola^2 / 4 / 100  [cm2]
' - As Min lido do SELE e dividido por 10
' - Status:
'   APROVADO    -> AsTotal >= AsMin
'   MARGEM 15%  -> AsTotal < AsMin, mas AsTotal * 1.15 >= AsMin
'   REPROVADO   -> AsTotal * 1.15 < AsMin
' ================================================================

' ================================================================
' MACROS PUBLICAS
' ================================================================

Public Sub Carregar_ARMPIL_CSV()
    On Error GoTo TrataErro

    Dim csvPath As String
    csvPath = RunPythonArmpilExtractor()
    If csvPath = "" Then GoTo Finaliza

    LoadArmpil csvPath
    MsgBox "ARMPIL extraido e carregado com sucesso.", vbInformation

Finaliza:
    Exit Sub

TrataErro:
    MsgBox "Erro ao carregar ARMPIL: " & Err.Description, vbExclamation
End Sub

Public Sub Carregar_ARMPIL_CSV_Manual()
    On Error GoTo TrataErro

    Dim csvPath As String
    csvPath = PickFilePath("Selecione o arquivo ARMPIL.csv", "CSV", "*.csv")
    If csvPath = "" Then GoTo Finaliza

    LoadArmpil csvPath
    MsgBox "ARMPIL carregado com sucesso.", vbInformation

Finaliza:
    Exit Sub

TrataErro:
    MsgBox "Erro ao carregar ARMPIL manualmente: " & Err.Description, vbExclamation
End Sub

Public Sub Carregar_SELE_LST()
    On Error GoTo TrataErro

    Dim selePath As String
    selePath = PickFilePath("Selecione o arquivo SELE.LST", "LST", "*.lst;*.LST")
    If selePath = "" Then GoTo Finaliza
    
    LoadSele selePath
    MsgBox "SELE carregado com sucesso.", vbInformation
    
Finaliza:
    Exit Sub

TrataErro:
    MsgBox "Erro ao carregar SELE: " & Err.Description, vbExclamation
End Sub

Public Sub Executar_Comparacao()
    On Error GoTo TrataErro

    CompareAndMark
    Exit Sub

TrataErro:
    MsgBox "Erro na comparacao: " & Err.Description, vbExclamation
End Sub

Public Sub Atualizar_ARMPIL_Manual()
    Dim state As AppState
    Dim wsArm As Worksheet
    Dim rowCount As Long
    Dim infoMessage As String
    Dim resultUpdated As Boolean
    Dim stage As String

    On Error GoTo TrataErro

    BeginExcelBatch state, "Atualizando ARMPIL manualmente..."

    stage = "localizar aba ARMPIL"
    Set wsArm = GetRequiredWorksheet("ARMPIL")
    stage = "preparar orientacao manual"
    SetArmpilManualHint wsArm

    stage = "normalizar dados manuais"
    If Not NormalizeManualArmpilEntries(wsArm, rowCount, infoMessage) Then
        MsgBox infoMessage, vbExclamation, "Atualizar ARMPIL manualmente"
        GoTo Finaliza
    End If

    stage = "atualizar RESULTADO"
    resultUpdated = CompareAndMark(False)
    stage = "ativar aba ARMPIL"
    wsArm.Activate

    If resultUpdated Then
        MsgBox _
            "ARMPIL atualizada com sucesso." & vbCrLf & vbCrLf & _
            "Registros reorganizados: " & rowCount & vbCrLf & _
            "RESULTADO atualizado automaticamente.", _
            vbInformation, _
            "Atualizar ARMPIL manualmente"
    Else
        MsgBox _
            "ARMPIL atualizada com sucesso." & vbCrLf & vbCrLf & _
            "Registros reorganizados: " & rowCount & vbCrLf & _
            "Nao foi possivel atualizar o RESULTADO.", _
            vbExclamation, _
            "Atualizar ARMPIL manualmente"
    End If

Finaliza:
    RestoreExcelBatch state
    Exit Sub

TrataErro:
    RestoreExcelBatch state
    MsgBox "Erro ao atualizar ARMPIL manualmente" & BuildStageSuffix(stage) & ": " & Err.Description, vbExclamation
End Sub

Public Sub Adicionar_Pilar()
    Dim state As AppState
    Dim wsArm As Worksheet
    Dim pilarNumber As String
    Dim pilarName As String
    Dim lanceValue As Long
    Dim qtyValue As Long
    Dim diamValue As Double
    Dim targetRow As Long
    Dim rowCount As Long
    Dim infoMessage As String
    Dim resultUpdated As Boolean
    Dim preferredPrefix As String
    Dim stage As String

    On Error GoTo TrataErro

    BeginExcelBatch state, "Adicionando pilar na ARMPIL..."

    stage = "localizar aba ARMPIL"
    Set wsArm = GetRequiredWorksheet("ARMPIL")
    stage = "identificar prefixo do pilar"
    preferredPrefix = GetPreferredPilarPrefix(wsArm)

    stage = "perguntar numero do pilar"
    pilarNumber = PromptPilarInput(wsArm, preferredPrefix)
    If pilarNumber = "" Then GoTo Finaliza

    stage = "normalizar numero do pilar"
    If Not TryNormalizeManualPilarInput(pilarNumber, preferredPrefix, pilarName) Then
        MsgBox "Numero de pilar invalido.", vbExclamation, "Adicionar pilar"
        GoTo Finaliza
    End If

    stage = "perguntar lance"
    If Not PromptPositiveLongValue( _
        "Informe o lance para " & pilarName & ".", _
        "Adicionar pilar", _
        GetSuggestedLanceForNewPilar(wsArm), _
        lanceValue _
    ) Then GoTo Finaliza

    stage = "perguntar quantidade"
    If Not PromptPositiveLongValue( _
        "Informe a quantidade (Qtd/Qf) para " & pilarName & ".", _
        "Adicionar pilar", _
        "", _
        qtyValue _
    ) Then GoTo Finaliza

    stage = "perguntar bitola"
    If Not PromptPositiveDoubleValue( _
        "Informe a bitola para " & pilarName & ".", _
        "Adicionar pilar", _
        "", _
        diamValue _
    ) Then GoTo Finaliza

    stage = "inserir linha temporaria"
    targetRow = GetLastArmpilDataRow(wsArm) + 1
    If targetRow < 6 Then targetRow = 6

    wsArm.Cells(targetRow, 2).Value = pilarName
    wsArm.Cells(targetRow, 3).Value = lanceValue
    wsArm.Cells(targetRow, 4).Value = qtyValue
    wsArm.Cells(targetRow, 5).Value = diamValue

    stage = "normalizar ARMPIL"
    If Not NormalizeManualArmpilEntries(wsArm, rowCount, infoMessage) Then
        MsgBox infoMessage, vbExclamation, "Adicionar pilar"
        GoTo Finaliza
    End If

    stage = "atualizar RESULTADO"
    resultUpdated = CompareAndMark(False)
    stage = "ativar aba ARMPIL"
    wsArm.Activate

    If resultUpdated Then
        MsgBox _
            pilarName & " adicionado com sucesso." & vbCrLf & vbCrLf & _
            "Registros reorganizados: " & rowCount & vbCrLf & _
            "RESULTADO atualizado automaticamente.", _
            vbInformation, _
            "Adicionar pilar"
    Else
        MsgBox _
            pilarName & " adicionado com sucesso." & vbCrLf & vbCrLf & _
            "Registros reorganizados: " & rowCount & vbCrLf & _
            "Nao foi possivel atualizar o RESULTADO.", _
            vbExclamation, _
            "Adicionar pilar"
    End If

Finaliza:
    RestoreExcelBatch state
    Exit Sub

TrataErro:
    RestoreExcelBatch state
    MsgBox "Erro ao adicionar pilar" & BuildStageSuffix(stage) & ": " & Err.Description, vbExclamation
End Sub

Public Sub Limpar_Todas_As_Tabelas()
    On Error GoTo TrataErro

    If MsgBox( _
        "Limpar todos os dados das abas ARMPIL, SELE e RESULTADO?", _
        vbQuestion + vbYesNo + vbDefaultButton2, _
        "Limpar tabelas" _
    ) <> vbYes Then
        Exit Sub
    End If

    ClearAllTables
    MsgBox "Tabelas limpas com sucesso.", vbInformation
    Exit Sub

TrataErro:
    MsgBox "Erro ao limpar tabelas: " & Err.Description, vbExclamation
End Sub
