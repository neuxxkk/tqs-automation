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
    Dim pilarInput As String
    Dim lanceInput As String
    Dim targetRow As Long
    Dim rowCount As Long
    Dim addedRowCount As Long
    Dim infoMessage As String
    Dim resultUpdated As Boolean
    Dim preferredPrefix As String
    Dim stage As String
    Dim selectedPilares() As String
    Dim selectedLances() As Long
    Dim expandedPilares() As String
    Dim expandedLances() As Long
    Dim qtyValues() As Long
    Dim diamValues() As Double
    Dim qtyValue As Long
    Dim diamValue As Double
    Dim qtySameForAll As Boolean
    Dim bitolaSameForAll As Boolean
    Dim previewText As String
    Dim qtyDefault As String
    Dim bitolaDefault As String
    Dim qtyListDefault As String
    Dim bitolaListDefault As String
    Dim dataIn() As Variant
    Dim i As Long
    Dim successLabel As String

    On Error GoTo TrataErro

    BeginExcelBatch state, "Adicionando pilar na ARMPIL..."

    stage = "localizar aba ARMPIL"
    Set wsArm = GetRequiredWorksheet("ARMPIL")
    stage = "identificar prefixo do pilar"
    preferredPrefix = GetPreferredPilarPrefix(wsArm)

    stage = "perguntar numero do pilar"
    pilarInput = PromptPilarInput(wsArm, preferredPrefix)
    If pilarInput = "" Then GoTo Finaliza

    stage = "normalizar numero do pilar"
    If Not TryParsePilarSelection(pilarInput, preferredPrefix, selectedPilares) Then
        MsgBox "Numero ou intervalo de pilar invalido.", vbExclamation, "Adicionar pilar"
        GoTo Finaliza
    End If

    Do
        stage = "perguntar lance"
        lanceInput = PromptLanceSelectionInput(wsArm)
        If lanceInput = "" Then GoTo Finaliza

        stage = "normalizar lance"
        If Not TryParsePositiveLongSelection(lanceInput, selectedLances) Then
            MsgBox "Lance ou intervalo invalido.", vbExclamation, "Adicionar pilar"
            GoTo Finaliza
        End If

        stage = "combinar pilar e lance"
        If TryExpandArmpilSelections(selectedPilares, selectedLances, expandedPilares, expandedLances, infoMessage) Then Exit Do

        MsgBox infoMessage, vbExclamation, "Adicionar pilar"
    Loop

    addedRowCount = GetStringArrayCount(expandedPilares)
    previewText = BuildArmpilRowSelectionPreview(expandedPilares, expandedLances, addedRowCount)
    qtyDefault = GetSuggestedQtyForNewPilar(wsArm)
    bitolaDefault = GetSuggestedBitolaForNewPilar(wsArm)

    If addedRowCount <= 1 Then
        stage = "perguntar quantidade"
        If Not PromptPositiveLongValue( _
            "Informe a quantidade (Qtd/Qf) para " & expandedPilares(1) & " / lance " & expandedLances(1) & ".", _
            "Adicionar pilar", _
            qtyDefault, _
            qtyValue _
        ) Then GoTo Finaliza

        ReDim qtyValues(1 To 1)
        qtyValues(1) = qtyValue

        stage = "perguntar bitola"
        If Not PromptPositiveDoubleValue( _
            "Informe a bitola para " & expandedPilares(1) & " / lance " & expandedLances(1) & ".", _
            "Adicionar pilar", _
            bitolaDefault, _
            diamValue _
        ) Then GoTo Finaliza

        ReDim diamValues(1 To 1)
        diamValues(1) = diamValue
    Else
        stage = "perguntar se quantidade repete"
        If Not PromptUniformValueChoice( _
            "A quantidade (Qtd/Qf) sera igual para as " & addedRowCount & " linhas?" & vbCrLf & vbCrLf & _
            previewText & vbCrLf & vbCrLf & _
            "Sim = usar um unico valor para todas" & vbCrLf & _
            "Nao = informar uma lista manual", _
            "Adicionar pilar", _
            qtySameForAll _
        ) Then GoTo Finaliza

        If qtySameForAll Then
            stage = "perguntar quantidade unica"
            If Not PromptPositiveLongValue( _
                "Informe a quantidade (Qtd/Qf) para todas as " & addedRowCount & " linhas.", _
                "Adicionar pilar", _
                qtyDefault, _
                qtyValue _
            ) Then GoTo Finaliza

            ReDim qtyValues(1 To addedRowCount)
            For i = 1 To addedRowCount
                qtyValues(i) = qtyValue
            Next i
        Else
            stage = "perguntar lista de quantidade"
            qtyListDefault = BuildRepeatedDefaultList(qtyDefault, addedRowCount)
            If Not PromptPositiveLongListValues( _
                "Informe as quantidades (Qtd/Qf) na mesma ordem das linhas abaixo, separadas por ';'." & vbCrLf & vbCrLf & _
                previewText & vbCrLf & vbCrLf & _
                "Ex.: " & IIf(qtyListDefault <> "", qtyListDefault, "4; 4; 6"), _
                "Adicionar pilar", _
                qtyListDefault, _
                addedRowCount, _
                qtyValues _
            ) Then GoTo Finaliza
        End If

        stage = "perguntar se bitola repete"
        If Not PromptUniformValueChoice( _
            "A bitola sera igual para as " & addedRowCount & " linhas?" & vbCrLf & vbCrLf & _
            previewText & vbCrLf & vbCrLf & _
            "Sim = usar um unico valor para todas" & vbCrLf & _
            "Nao = informar uma lista manual", _
            "Adicionar pilar", _
            bitolaSameForAll _
        ) Then GoTo Finaliza

        If bitolaSameForAll Then
            stage = "perguntar bitola unica"
            If Not PromptPositiveDoubleValue( _
                "Informe a bitola para todas as " & addedRowCount & " linhas.", _
                "Adicionar pilar", _
                bitolaDefault, _
                diamValue _
            ) Then GoTo Finaliza

            ReDim diamValues(1 To addedRowCount)
            For i = 1 To addedRowCount
                diamValues(i) = diamValue
            Next i
        Else
            stage = "perguntar lista de bitola"
            bitolaListDefault = BuildRepeatedDefaultList(bitolaDefault, addedRowCount)
            If Not PromptPositiveDoubleListValues( _
                "Informe as bitolas na mesma ordem das linhas abaixo, separadas por ';'." & vbCrLf & vbCrLf & _
                previewText & vbCrLf & vbCrLf & _
                "Ex.: " & IIf(bitolaListDefault <> "", bitolaListDefault, "10; 12,5; 16"), _
                "Adicionar pilar", _
                bitolaListDefault, _
                addedRowCount, _
                diamValues _
            ) Then GoTo Finaliza
        End If
    End If

    stage = "inserir linhas temporarias"
    targetRow = GetLastArmpilDataRow(wsArm) + 1
    If targetRow < 6 Then targetRow = 6

    ReDim dataIn(1 To addedRowCount, 1 To 4)
    For i = 1 To addedRowCount
        dataIn(i, 1) = expandedPilares(i)
        dataIn(i, 2) = expandedLances(i)
        dataIn(i, 3) = qtyValues(i)
        dataIn(i, 4) = diamValues(i)
    Next i
    wsArm.Range("B" & targetRow).Resize(addedRowCount, 4).Value = dataIn

    stage = "normalizar ARMPIL"
    If Not NormalizeManualArmpilEntries(wsArm, rowCount, infoMessage) Then
        MsgBox infoMessage, vbExclamation, "Adicionar pilar"
        GoTo Finaliza
    End If

    stage = "atualizar RESULTADO"
    resultUpdated = CompareAndMark(False)
    stage = "ativar aba ARMPIL"
    wsArm.Activate

    If addedRowCount = 1 Then
        successLabel = expandedPilares(1) & " / lance " & expandedLances(1)
        If resultUpdated Then
            MsgBox _
                successLabel & " adicionado com sucesso." & vbCrLf & vbCrLf & _
                "Registros reorganizados: " & rowCount & vbCrLf & _
                "RESULTADO atualizado automaticamente.", _
                vbInformation, _
                "Adicionar pilar"
        Else
            MsgBox _
                successLabel & " adicionado com sucesso." & vbCrLf & vbCrLf & _
                "Registros reorganizados: " & rowCount & vbCrLf & _
                "Nao foi possivel atualizar o RESULTADO.", _
                vbExclamation, _
                "Adicionar pilar"
        End If
    Else
        successLabel = addedRowCount & " linhas"
        If resultUpdated Then
            MsgBox _
                successLabel & " adicionadas com sucesso." & vbCrLf & vbCrLf & _
                "Registros reorganizados: " & rowCount & vbCrLf & _
                "RESULTADO atualizado automaticamente.", _
                vbInformation, _
                "Adicionar pilar"
        Else
            MsgBox _
                successLabel & " adicionadas com sucesso." & vbCrLf & vbCrLf & _
                "Registros reorganizados: " & rowCount & vbCrLf & _
                "Nao foi possivel atualizar o RESULTADO.", _
                vbExclamation, _
                "Adicionar pilar"
        End If
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
