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
    MsgBox "ARMPIL extraído e carregado com sucesso.", vbInformation

Finaliza:
    Exit Sub

TrataErro:
    MsgBox "Erro ao carregar ARMPIL: " & Err.Description, vbExclamation
End Sub

Public Sub Carregar_ARMPIL_CSV_Manual()
    On Error GoTo TrataErro

    Dim fd As FileDialog
    Set fd = Application.FileDialog(msoFileDialogFilePicker)

    fd.Title = "Selecione o arquivo ARMPIL.csv"
    fd.Filters.Clear
    fd.Filters.Add "CSV", "*.csv"
    fd.Filters.Add "Todos", "*.*"
    fd.AllowMultiSelect = False

    If fd.Show <> -1 Then GoTo Finaliza

    LoadArmpil fd.SelectedItems(1)
    MsgBox "ARMPIL carregado com sucesso.", vbInformation

Finaliza:
    Exit Sub

TrataErro:
    MsgBox "Erro ao carregar ARMPIL manualmente: " & Err.Description, vbExclamation
End Sub

Public Sub Carregar_SELE_LST()
    On Error GoTo TrataErro

    Dim fd As FileDialog
    Set fd = Application.FileDialog(msoFileDialogFilePicker)
    
    fd.Title = "Selecione o arquivo SELE.LST"
    fd.Filters.Clear
    fd.Filters.Add "LST", "*.lst;*.LST"
    fd.Filters.Add "Todos", "*.*"
    fd.AllowMultiSelect = False
    
    If fd.Show <> -1 Then GoTo Finaliza
    
    LoadSele fd.SelectedItems(1)
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
    Dim oldCalc As XlCalculation
    Dim oldScreen As Boolean
    Dim oldEvents As Boolean
    Dim oldStatusBar As Variant
    Dim wsArm As Worksheet
    Dim rowCount As Long
    Dim infoMessage As String
    Dim resultUpdated As Boolean
    Dim stage As String

    oldCalc = Application.Calculation
    oldScreen = Application.ScreenUpdating
    oldEvents = Application.EnableEvents
    oldStatusBar = Application.StatusBar

    On Error GoTo TrataErro

    Application.ScreenUpdating = False
    Application.EnableEvents = False
    Application.Calculation = xlCalculationManual
    Application.StatusBar = "Atualizando ARMPIL manualmente..."

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
    Application.StatusBar = oldStatusBar
    Application.Calculation = oldCalc
    Application.ScreenUpdating = oldScreen
    Application.EnableEvents = oldEvents
    Exit Sub

TrataErro:
    Application.StatusBar = oldStatusBar
    Application.Calculation = oldCalc
    Application.ScreenUpdating = oldScreen
    Application.EnableEvents = oldEvents
    MsgBox "Erro ao atualizar ARMPIL manualmente" & BuildStageSuffix(stage) & ": " & Err.Description, vbExclamation
End Sub

Public Sub Adicionar_Pilar()
    Dim oldCalc As XlCalculation
    Dim oldScreen As Boolean
    Dim oldEvents As Boolean
    Dim oldStatusBar As Variant
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

    oldCalc = Application.Calculation
    oldScreen = Application.ScreenUpdating
    oldEvents = Application.EnableEvents
    oldStatusBar = Application.StatusBar

    On Error GoTo TrataErro

    Application.ScreenUpdating = False
    Application.EnableEvents = False
    Application.Calculation = xlCalculationManual
    Application.StatusBar = "Adicionando pilar na ARMPIL..."

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
    Application.StatusBar = oldStatusBar
    Application.Calculation = oldCalc
    Application.ScreenUpdating = oldScreen
    Application.EnableEvents = oldEvents
    Exit Sub

TrataErro:
    Application.StatusBar = oldStatusBar
    Application.Calculation = oldCalc
    Application.ScreenUpdating = oldScreen
    Application.EnableEvents = oldEvents
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

' ================================================================
' CARREGA ARMPIL - OTIMIZADO
' Mantém As Total e Chave como fórmulas na planilha
' Esperado: Pilar, Lance, Qtd(Qf), Bitola(mm)
' Se vier coluna extra (As Total), ela é ignorada.
' ================================================================
Private Sub LoadArmpil(ByVal path As String)
    Dim ws As Worksheet
    Set ws = ThisWorkbook.Sheets("ARMPIL")

    Dim oldCalc As XlCalculation
    Dim oldScreen As Boolean
    Dim oldEvents As Boolean
    Dim oldStatusBar As Variant

    oldCalc = Application.Calculation
    oldScreen = Application.ScreenUpdating
    oldEvents = Application.EnableEvents
    oldStatusBar = Application.StatusBar

    On Error GoTo TrataErro

    Application.ScreenUpdating = False
    Application.EnableEvents = False
    Application.Calculation = xlCalculationManual
    Application.StatusBar = "Carregando ARMPIL..."

    ClearARMPIL ws
    SetArmpilManualHint ws

    Dim lines As Variant
    lines = ReadAllNonEmptyLines(path)

    If Not IsArray(lines) Then GoTo SaidaSegura
    If UBound(lines) < LBound(lines) Then GoTo SaidaSegura

    Dim delim As String
    delim = DetectDelim(CStr(lines(LBound(lines))))

    Dim startIdx As Long
    startIdx = LBound(lines)

    Dim firstField As String
    firstField = LCase$(Trim$(Replace(Split(CStr(lines(LBound(lines))), delim)(0), Chr$(34), "")))
    If firstField = "pilar" Then startIdx = startIdx + 1

    Dim maxRows As Long
    maxRows = UBound(lines) - startIdx + 1
    If maxRows <= 0 Then GoTo SaidaSegura

    Dim dataOut() As Variant
    ReDim dataOut(1 To maxRows, 1 To 4)

    Dim i As Long
    Dim outRow As Long
    outRow = 0

    Dim parts() As String
    Dim pilar As String

    For i = startIdx To UBound(lines)
        parts = Split(CStr(lines(i)), delim)

        If UBound(parts) >= 3 Then
            pilar = NormalizePilarName(CleanCSV(parts(0)))

            If pilar <> "" And LCase$(pilar) <> "pilar" Then
                outRow = outRow + 1

                dataOut(outRow, 1) = pilar
                dataOut(outRow, 2) = CLng(Val(CleanCSV(parts(1))))
                dataOut(outRow, 3) = CDbl(Val(CleanCSV(parts(2))))
                dataOut(outRow, 4) = CDbl(Val(CleanCSV(parts(3))))
            End If
        End If
    Next i

    If outRow = 0 Then GoTo SaidaSegura

    ' Escreve B:E de uma vez
    ws.Range("B6").Resize(outRow, 4).Value = dataOut

    ws.Range("F6:F" & 5 + outRow).FormulaR1C1 = "=RC[-2]*PI()*(RC[-1]^2)/4/100"
    ws.Range("G6:G" & 5 + outRow).FormulaR1C1 = "=UPPER(TRIM(RC[-5]))&""|""&RC[-4]"
    ws.Range("F6:G" & 5 + outRow).Calculate

    SortSheetRangeByPilarLance ws, 6, 5 + outRow, 2, 7, 2, 3, 8
    ws.Range("F6:G" & 5 + outRow).Calculate

    ws.Range("C6:C" & 5 + outRow).NumberFormat = "0"
    ws.Range("D6:E" & 5 + outRow).NumberFormat = "0.00"
    ws.Range("F6:F" & 5 + outRow).NumberFormat = "0.00"

    ApplyArmpilFormatting ws, 6, 5 + outRow

    ws.Cells(4, 2).Value = "  Carregado: " & outRow & " registros  |  delimitador: [" & delim & "]  |  " & path

SaidaSegura:
    Application.StatusBar = oldStatusBar
    Application.Calculation = oldCalc
    Application.ScreenUpdating = oldScreen
    Application.EnableEvents = oldEvents
    Exit Sub

TrataErro:
    Application.StatusBar = oldStatusBar
    Application.Calculation = oldCalc
    Application.ScreenUpdating = oldScreen
    Application.EnableEvents = oldEvents
    MsgBox "Erro em LoadArmpil: " & Err.Description, vbExclamation
End Sub


' ================================================================
' CARREGA SELE.LST  –  versão otimizada
' ================================================================
Private Sub LoadSele(ByVal path As String)
    Dim oldCalc As XlCalculation
    Dim oldScreen As Boolean
    Dim oldEvents As Boolean

    oldCalc = Application.Calculation
    oldScreen = Application.ScreenUpdating
    oldEvents = Application.EnableEvents

    Application.ScreenUpdating = False
    Application.Calculation = xlCalculationManual
    Application.EnableEvents = False

    On Error GoTo Cleanup

    Dim lines As Variant
    lines = ReadAllNonEmptyLines(path)
    If Not IsArray(lines) Then GoTo Cleanup
    If UBound(lines) < LBound(lines) Then GoTo Cleanup

    Dim lancesDict As Object
    Dim lanceTitles As Object
    Set lancesDict = CreateObject("Scripting.Dictionary")
    Set lanceTitles = CreateObject("Scripting.Dictionary")

    Dim currentPilar As String: currentPilar = ""
    Dim i As Long, lanceNum As Long, asVal As Double
    Dim lanceTitle As String

    For i = LBound(lines) To UBound(lines)
        Dim line As String: line = Trim$(lines(i))
        If line = "" Then GoTo P1Next

        If Left$(line, 6) = "PILAR:" Then
            currentPilar = ExtractSelePilarName(line)
            GoTo P1Next
        End If

        If currentPilar = "" Then GoTo P1Next
        If Not IsDataLine(line) Then GoTo P1Next
        If Not ParseSeleLine(line, lanceNum, asVal) Then GoTo P1Next

        If Not lancesDict.Exists(lanceNum) Then lancesDict(lanceNum) = True
        If Not lanceTitles.Exists(lanceNum) Then
            lanceTitle = ExtractSeleLanceTitle(line)
            If lanceTitle <> "" Then lanceTitles(lanceNum) = lanceTitle
        End If
P1Next:
    Next i

    If lancesDict.count = 0 Then GoTo Cleanup

    Dim keys As Variant: keys = lancesDict.keys
    SortNumericVariantArray keys

    Dim lanceList As String
    lanceList = JoinVariantList(keys)

    Dim suggestedList As String
    suggestedList = BuildSuggestedSeleLances(keys)

    Dim lanceTitleList As String
    Dim suggestedTitleList As String
    Dim lancePromptList As String
    Dim suggestedPromptList As String
    lanceTitleList = BuildLanceTitleList(keys, lanceTitles)
    suggestedTitleList = BuildLanceTitleListFromCsv(suggestedList, lanceTitles)
    lancePromptList = BuildPromptLanceList(keys, lanceTitles)
    suggestedPromptList = BuildPromptLanceListFromCsv(suggestedList, lanceTitles)

    Dim resp As Variant
    resp = PromptSeleLanceFilter(lanceList, suggestedList, lancePromptList, suggestedPromptList)
    If IsDialogCancelled(resp) Then GoTo Cleanup

    Dim filterSet As Object
    Set filterSet = BuildLanceFilterSet(Trim$(CStr(resp)))

    Dim filterActive As Boolean
    filterActive = (filterSet.count > 0) And (filterSet.count < lancesDict.count)

    Dim maxRows As Long: maxRows = UBound(lines) - LBound(lines) + 1

    Dim arrPilar() As String:  ReDim arrPilar(1 To maxRows)
    Dim arrLance() As Long:    ReDim arrLance(1 To maxRows)
    Dim arrAs()    As Double:  ReDim arrAs(1 To maxRows)

    Dim rowCount As Long:  rowCount = 0
    currentPilar = ""

    For i = LBound(lines) To UBound(lines)
        line = Trim$(lines(i))
        If line = "" Then GoTo P2Next

        If Left$(line, 6) = "PILAR:" Then
            currentPilar = ExtractSelePilarName(line)
            GoTo P2Next
        End If

        If currentPilar = "" Then GoTo P2Next
        If Not IsDataLine(line) Then GoTo P2Next
        If Not ParseSeleLine(line, lanceNum, asVal) Then GoTo P2Next

        If filterActive Then
            If Not filterSet.Exists(lanceNum) Then GoTo P2Next
        End If

        rowCount = rowCount + 1
        arrPilar(rowCount) = NormalizePilarName(currentPilar)
        arrLance(rowCount) = lanceNum
        arrAs(rowCount) = asVal / 10#
P2Next:
    Next i

    Dim ws As Worksheet
    Set ws = ThisWorkbook.Sheets("SELE")
    Call ClearSELE(ws)

    If rowCount = 0 Then
        ws.Cells(4, 2).value = "  Nenhum registro para os níveis selecionados."
        GoTo Cleanup
    End If

    ' Monta arrays 2-D para escrita em bloco (uma chamada por coluna)
    Dim colB() As Variant: ReDim colB(1 To rowCount, 1 To 1)
    Dim colC() As Variant: ReDim colC(1 To rowCount, 1 To 1)
    Dim colD() As Variant: ReDim colD(1 To rowCount, 1 To 1)
    Dim colE() As Variant: ReDim colE(1 To rowCount, 1 To 1)

    For i = 1 To rowCount
        colB(i, 1) = arrPilar(i)
        colC(i, 1) = arrLance(i)
        colD(i, 1) = arrAs(i)
        colE(i, 1) = BuildPilarKey(arrPilar(i), arrLance(i))
    Next i

    Dim startRow As Long: startRow = 6
    Dim endRow   As Long: endRow = startRow + rowCount - 1

    With ws
        .Range(.Cells(startRow, 2), .Cells(endRow, 2)).value = colB
        .Range(.Cells(startRow, 3), .Cells(endRow, 3)).value = colC
        .Range(.Cells(startRow, 4), .Cells(endRow, 4)).value = colD
        .Range(.Cells(startRow, 4), .Cells(endRow, 4)).NumberFormat = "0.00"
        .Range(.Cells(startRow, 5), .Cells(endRow, 5)).value = colE
    End With

    SortSheetRangeByPilarLance ws, startRow, endRow, 2, 5, 2, 3, 6
    ApplySeleFormatting ws, startRow, endRow

    ws.Cells(4, 2).value = "  Carregado: " & rowCount & " registros  |  Lances: " & CompactPromptText(lanceTitleList, 160) & "  |  " & path

Cleanup:
    Application.EnableEvents = oldEvents
    Application.Calculation = oldCalc
    Application.ScreenUpdating = oldScreen
    If Err.Number <> 0 Then
        MsgBox "Erro em LoadSele: " & Err.Description, vbExclamation
    End If
End Sub

' ================================================================
' COMPARACAO
' ================================================================
Private Function CompareAndMark(Optional ByVal showSuccessMessage As Boolean = True) As Boolean
    Dim oldCalc As XlCalculation
    Dim oldScreen As Boolean
    Dim oldEvents As Boolean

    oldCalc = Application.Calculation
    oldScreen = Application.ScreenUpdating
    oldEvents = Application.EnableEvents

    Application.ScreenUpdating = False
    Application.Calculation = xlCalculationManual
    Application.EnableEvents = False

    On Error GoTo Cleanup

    Dim wsArm As Worksheet, wsSel As Worksheet, wsRes As Worksheet
    Set wsArm = GetRequiredWorksheet("ARMPIL")
    Set wsSel = GetRequiredWorksheet("SELE")
    Set wsRes = GetRequiredWorksheet("RESULTADO")

    ClearResultsPermanent wsRes

    Dim lastArm As Long, lastSel As Long
    lastArm = wsArm.Cells(wsArm.Rows.count, 2).End(xlUp).Row
    lastSel = wsSel.Cells(wsSel.Rows.count, 2).End(xlUp).Row

    If lastArm < 6 And lastSel < 6 Then
        MsgBox "Nenhum dado carregado em ARMPIL ou SELE.", vbExclamation
        GoTo Cleanup
    End If

    If lastArm < 6 Then
        MsgBox "Nenhum dado carregado em ARMPIL.", vbExclamation
        GoTo Cleanup
    End If

    If lastSel < 6 Then
        MsgBox "Nenhum dado carregado em SELE.", vbExclamation
        GoTo Cleanup
    End If

    Dim dict As Object
    Set dict = CreateObject("Scripting.Dictionary")

    If lastArm >= 6 Then
        AddKeysFromData dict, wsArm.Range("B6:C" & lastArm).Value2
    End If
    If lastSel >= 6 Then
        AddKeysFromData dict, wsSel.Range("B6:C" & lastSel).Value2
    End If

    If dict.count = 0 Then
        MsgBox "Nenhuma chave válida encontrada para comparar.", vbExclamation
        GoTo Cleanup
    End If

    Dim resCount As Long
    resCount = dict.count

    Dim dataOut() As Variant
    ReDim dataOut(1 To resCount, 1 To 2)

    Dim i As Long
    Dim k As Variant
    i = 0
    For Each k In dict.keys
        i = i + 1
        dataOut(i, 1) = dict(k)(0)
        dataOut(i, 2) = dict(k)(1)
    Next k

    Dim firstResRow As Long
    Dim lastResRow As Long
    firstResRow = 9
    lastResRow = firstResRow + resCount - 1

    With wsRes
        .Range(.Cells(firstResRow, 2), .Cells(lastResRow, 3)).Value2 = dataOut
        .Range(.Cells(firstResRow, 4), .Cells(lastResRow, 4)).FormulaR1C1 = "=UPPER(TRIM(RC[-2]))&""|""&RC[-1]"

        If lastArm >= 6 Then
            .Range(.Cells(firstResRow, 5), .Cells(lastResRow, 5)).FormulaR1C1 = _
                "=IFERROR(INDEX(ARMPIL!R6C4:R" & lastArm & "C4,MATCH(RC4,ARMPIL!R6C7:R" & lastArm & "C7,0)),"""")"
            .Range(.Cells(firstResRow, 6), .Cells(lastResRow, 6)).FormulaR1C1 = _
                "=IFERROR(INDEX(ARMPIL!R6C5:R" & lastArm & "C5,MATCH(RC4,ARMPIL!R6C7:R" & lastArm & "C7,0)),"""")"
            .Range(.Cells(firstResRow, 7), .Cells(lastResRow, 7)).FormulaR1C1 = _
                "=IFERROR(INDEX(ARMPIL!R6C6:R" & lastArm & "C6,MATCH(RC4,ARMPIL!R6C7:R" & lastArm & "C7,0)),"""")"
        End If

        If lastSel >= 6 Then
            .Range(.Cells(firstResRow, 8), .Cells(lastResRow, 8)).FormulaR1C1 = _
                "=IFERROR(INDEX(SELE!R6C4:R" & lastSel & "C4,MATCH(RC4,SELE!R6C5:R" & lastSel & "C5,0)),"""")"
        End If

        .Range(.Cells(firstResRow, 9), .Cells(lastResRow, 9)).FormulaR1C1 = _
            "=IF(OR(RC[-2]="""",RC[-1]=""""),"""",RC[-2]-RC[-1])"
        .Range(.Cells(firstResRow, 10), .Cells(lastResRow, 10)).FormulaR1C1 = _
            "=IF(OR(RC[-3]="""",RC[-2]=""""),""SEM MATCH"",IF(RC[-3]>=RC[-2],""APROVADO"",IF(RC[-3]*1.15>=RC[-2],""MARGEM 15%"",""REPROVADO"")))"
        .Range(.Cells(firstResRow, 4), .Cells(lastResRow, 10)).Calculate
    End With

    SortSheetRangeByPilarLance wsRes, firstResRow, lastResRow, 2, 10, 2, 3, 11
    wsRes.Range(wsRes.Cells(firstResRow, 4), wsRes.Cells(lastResRow, 10)).Calculate

    FormatResultadoRange wsRes, firstResRow, lastResRow
    AtualizarResumoResultado wsRes, lastResRow
    ConfigurarFormatacaoCondicionalResultado wsRes, lastResRow
    CompareAndMark = True

    If showSuccessMessage Then
        wsRes.Activate
        MsgBox "Resultado preparado com fórmulas permanentes.", vbInformation
    End If

Cleanup:
    Application.EnableEvents = oldEvents
    Application.Calculation = oldCalc
    Application.ScreenUpdating = oldScreen
    If Err.Number <> 0 Then
        MsgBox "Erro na comparacao: " & Err.Description, vbExclamation
    End If
End Function

Private Function RunPythonArmpilExtractor() As String
    Dim oldStatusBar As Variant
    Dim errNum As Long
    Dim errDesc As String
    Dim pdfPath As String
    Dim levelsCsv As String
    Dim allLevelsCsv As String
    Dim lanceMap As String
    Dim stage As String

    oldStatusBar = Application.StatusBar
    Application.StatusBar = "Executando extrator ARMPIL..."

    On Error GoTo Cleanup

    stage = "selecionar PDF"
    pdfPath = PickArmpilPdfPath()
    If pdfPath = "" Then GoTo Cleanup

    Dim scriptPath As String
    stage = "localizar script Python"
    scriptPath = GetArmpilScriptPath()
    If scriptPath = "" Then GoTo Cleanup

    Dim pythonExe As String
    Dim pythonArgs As String
    stage = "localizar interpretador Python"
    If Not GetPythonCommand(pythonExe, pythonArgs) Then
        Err.Raise vbObjectError + 2000, , "Python não encontrado. Instale o Python ou ajuste o launcher no VBA."
    End If

    stage = "ler niveis do PDF"
    levelsCsv = GetArmpilLevels(pythonExe, pythonArgs, scriptPath, pdfPath, allLevelsCsv)

    If levelsCsv <> "" Then
        stage = "mapear lances"
        lanceMap = ResolveArmpilLanceMap(levelsCsv, allLevelsCsv)
        If lanceMap = "" Then GoTo Cleanup
    ElseIf allLevelsCsv <> "" Then
        MsgBox BuildArmpilLevelsPrompt(allLevelsCsv, levelsCsv) & vbCrLf & vbCrLf & _
            "Nenhum lance/nivel com armadura longitudinal foi identificado para mapear.", _
            vbInformation, _
            "Mapear lances ARMPIL"
    End If

    Dim shellObj As Object
    Dim exitCode As Long
    Dim resultFile As String
    Dim launcherFile As String
    Dim resultText As String

    resultFile = Environ$("TEMP") & Application.PathSeparator & "armpil_result_" & Format$(Now, "yyyymmdd_hhnnss") & ".txt"
    launcherFile = Environ$("TEMP") & Application.PathSeparator & "armpil_run_" & Format$(Now, "yyyymmdd_hhnnss") & ".cmd"

    stage = "executar extrator Python"
    WriteTextFile launcherFile, BuildPythonLauncherScript(pythonExe, pythonArgs, scriptPath, resultFile, pdfPath, lanceMap)

    Set shellObj = CreateObject("WScript.Shell")
    exitCode = shellObj.Run("cmd.exe /d /c " & QuotePath(launcherFile), 0, True)

    stage = "ler retorno do extrator"
    resultText = ReadTextFileSafe(resultFile)
    If Dir$(resultFile) <> "" Then Kill resultFile
    If Dir$(launcherFile) <> "" Then Kill launcherFile

    If exitCode <> 0 Then
        If InStr(1, resultText, "[CANCELADO]", vbTextCompare) > 0 Then
            GoTo Cleanup
        End If

        Err.Raise vbObjectError + 2001, , BuildPythonErrorMessage(resultText, launcherFile)
    End If

    RunPythonArmpilExtractor = ExtractTaggedValue(resultText, "CSV_OUTPUT=")
    If RunPythonArmpilExtractor = "" Then
        Err.Raise vbObjectError + 2002, , "O script Python terminou sem informar o CSV gerado."
    End If

    If Not FileExists(RunPythonArmpilExtractor) Then
        Err.Raise vbObjectError + 2003, , "CSV gerado não encontrado:" & vbCrLf & RunPythonArmpilExtractor
    End If

Cleanup:
    errNum = Err.Number
    errDesc = Err.Description
    Application.StatusBar = oldStatusBar
    If errNum <> 0 Then
        If stage <> "" Then
            Err.Raise errNum, , "Etapa '" & stage & "': " & errDesc
        Else
            Err.Raise errNum, , errDesc
        End If
    End If
End Function

Private Function GetArmpilLevels(ByVal pythonExe As String, ByVal pythonArgs As String, ByVal scriptPath As String, ByVal pdfPath As String, ByRef allLevelsCsv As String) As String
    Dim shellObj As Object
    Dim exitCode As Long
    Dim resultFile As String
    Dim launcherFile As String
    Dim resultText As String

    resultFile = Environ$("TEMP") & Application.PathSeparator & "armpil_levels_" & Format$(Now, "yyyymmdd_hhnnss") & ".txt"
    launcherFile = Environ$("TEMP") & Application.PathSeparator & "armpil_levels_" & Format$(Now, "yyyymmdd_hhnnss") & ".cmd"

    WriteTextFile launcherFile, BuildPythonLauncherScript(pythonExe, pythonArgs, scriptPath, resultFile, pdfPath, "", "--levels")

    Set shellObj = CreateObject("WScript.Shell")
    exitCode = shellObj.Run("cmd.exe /d /c " & QuotePath(launcherFile), 0, True)

    resultText = ReadTextFileSafe(resultFile)
    If Dir$(resultFile) <> "" Then Kill resultFile
    If Dir$(launcherFile) <> "" Then Kill launcherFile

    If exitCode <> 0 Then
        Err.Raise vbObjectError + 2006, , BuildPythonErrorMessage(resultText, launcherFile)
    End If

    GetArmpilLevels = ExtractTaggedValue(resultText, "LEVELS=")
    allLevelsCsv = ExtractTaggedValue(resultText, "ALL_LEVELS=")
    If allLevelsCsv = "" Then allLevelsCsv = GetArmpilLevels
End Function

Private Function ResolveArmpilLanceMap(ByVal levelsCsv As String, Optional ByVal allLevelsCsv As String = "") As String
    Dim defaultLances As String
    Dim defaultMap As String
    Dim defaultPairs As String
    Dim identifiedLevelsCsv As String
    Dim manualLevelsCsv As String
    Dim levelCount As Long
    Dim choice As VbMsgBoxResult
    Dim prompt As String
    Dim resp As String
    Dim mapText As String
    Dim manualDefault As String
    Dim defaultDisplay As String
    Dim suggestionLabel As String
    Dim knownLancesCsv As String

    levelCount = CountCsvItems(levelsCsv)
    If levelCount <= 0 Then Exit Function

    identifiedLevelsCsv = Trim$(levelsCsv)
    manualLevelsCsv = Trim$(allLevelsCsv)
    If manualLevelsCsv = "" Then manualLevelsCsv = identifiedLevelsCsv

    knownLancesCsv = GetKnownLancesForPython()
    defaultLances = GetSuggestedArmpilLances(identifiedLevelsCsv, knownLancesCsv)
    defaultMap = BuildLanceMapFromLists(identifiedLevelsCsv, defaultLances)
    defaultPairs = BuildLanceLevelListFromMap(defaultMap)
    If knownLancesCsv <> "" Then
        suggestionLabel = "Mapa sugerido pelos lances ja carregados no SELE:"
    Else
        suggestionLabel = "Mapa sugerido pelo padrao local (SELE ainda nao carregado):"
    End If
    defaultDisplay = defaultPairs
    If Trim$(defaultDisplay) = "" Then
        defaultDisplay = "(nenhuma sugestao automatica encontrada)"
    End If

    If defaultMap <> "" Then
        choice = MsgBox( _
            "Niveis uteis identificados pelo script:" & vbCrLf & _
            "  " & FormatLevelsForPrompt(identifiedLevelsCsv) & vbCrLf & vbCrLf & _
            suggestionLabel & vbCrLf & _
            "  " & defaultDisplay & vbCrLf & vbCrLf & _
            "Sim = usar sugestao" & vbCrLf & _
            "Nao = mapear manualmente com todos os niveis detectados" & vbCrLf & _
            "Cancelar = cancelar", _
            vbQuestion + vbYesNoCancel, _
            "Mapear lances ARMPIL" _
        )

        If choice = vbYes Then
            ResolveArmpilLanceMap = defaultMap
            Exit Function
        End If

        If choice = vbCancel Then Exit Function
    Else
        choice = MsgBox( _
            "Niveis uteis identificados pelo script:" & vbCrLf & _
            "  " & FormatLevelsForPrompt(identifiedLevelsCsv) & vbCrLf & vbCrLf & _
            suggestionLabel & vbCrLf & _
            "  " & defaultDisplay & vbCrLf & vbCrLf & _
            "OK = mapear manualmente com todos os niveis detectados" & vbCrLf & _
            "Cancelar = cancelar", _
            vbInformation + vbOKCancel, _
            "Mapear lances ARMPIL" _
        )

        If choice <> vbOK Then Exit Function
    End If

    manualDefault = BuildLanceEntriesForLevels(manualLevelsCsv, defaultMap)
    If Trim$(manualDefault) = "" Then manualDefault = BuildLanceEntriesForLevels(manualLevelsCsv, BuildLanceMapFromLists(manualLevelsCsv, GetSuggestedArmpilLances(manualLevelsCsv, knownLancesCsv)))
    If Trim$(manualDefault) = "" Then manualDefault = defaultLances
    If Trim$(manualDefault) = "" Then manualDefault = defaultPairs

    prompt = BuildArmpilManualPrompt(manualLevelsCsv, identifiedLevelsCsv, defaultPairs)

    Do
        resp = InputBox(prompt, "Mapear lances ARMPIL", manualDefault)
        If Trim$(resp) = "" Then Exit Function

        mapText = BuildLanceMapFromLists(manualLevelsCsv, resp)
        If mapText <> "" Then
            ResolveArmpilLanceMap = mapText
            Exit Function
        End If

        MsgBox BuildArmpilMapErrorMessage(defaultPairs), vbExclamation, "Mapear lances ARMPIL"
    Loop
End Function

Private Function IsDialogCancelled(ByVal value As Variant) As Boolean
    If VarType(value) = vbBoolean Then
        IsDialogCancelled = (CBool(value) = False)
    Else
        IsDialogCancelled = False
    End If
End Function

Private Function BuildExplicitLanceMap(ByVal rawText As String) As String
    Dim normalized As String
    Dim parts() As String
    Dim i As Long
    Dim chunk As String
    Dim sepPos As Long
    Dim isLanceLevelPair As Boolean
    Dim levelText As String
    Dim lanceText As String

    normalized = Trim$(rawText)
    normalized = Replace(normalized, "->", "=")
    normalized = Replace(normalized, "=>", "=")
    normalized = Replace(normalized, vbCrLf, ";")
    normalized = Replace(normalized, vbCr, ";")
    normalized = Replace(normalized, vbLf, ";")
    normalized = Replace(normalized, " e ", ";")

    parts = Split(normalized, ";")

    For i = LBound(parts) To UBound(parts)
        chunk = Trim$(parts(i))
        If chunk = "" Then GoTo NextPair

        sepPos = InStr(1, chunk, "=", vbTextCompare)
        isLanceLevelPair = False
        If InStr(1, chunk, ":", vbTextCompare) > 0 Then
            sepPos = InStr(1, chunk, ":", vbTextCompare)
            isLanceLevelPair = True
        End If

        If sepPos <= 1 Or sepPos >= Len(chunk) Then Exit Function

        If isLanceLevelPair Then
            lanceText = Trim$(Left$(chunk, sepPos - 1))
            levelText = Trim$(Mid$(chunk, sepPos + 1))
        Else
            levelText = Trim$(Left$(chunk, sepPos - 1))
            lanceText = Trim$(Mid$(chunk, sepPos + 1))

            If LooksLikeLanceLevelPair(levelText, lanceText) Then
                Dim tmpText As String
                tmpText = levelText
                levelText = lanceText
                lanceText = tmpText
            End If
        End If

        If Left$(levelText, 1) = "+" Then levelText = Mid$(levelText, 2)
        levelText = Replace(levelText, ",", ".")

        If levelText = "" Then Exit Function
        If Not IsNumeric(lanceText) Then Exit Function
        If CLng(Val(lanceText)) = 0 Then GoTo NextPair

        If BuildExplicitLanceMap <> "" Then BuildExplicitLanceMap = BuildExplicitLanceMap & ";"
        BuildExplicitLanceMap = BuildExplicitLanceMap & levelText & "=" & CLng(lanceText)
NextPair:
    Next i
End Function

Private Function LooksLikeLanceLevelPair(ByVal leftText As String, ByVal rightText As String) As Boolean
    Dim leftValue As Double
    Dim rightValue As Double

    leftText = Replace(Replace(Trim$(leftText), "+", ""), ",", ".")
    rightText = Replace(Replace(Trim$(rightText), "+", ""), ",", ".")

    leftValue = Val(leftText)
    rightValue = Val(rightText)
    If leftValue <= 0# Or rightValue <= 0# Then Exit Function

    LooksLikeLanceLevelPair = (leftValue < 200# And rightValue >= 200#)
End Function

Private Function IsExplicitLanceMapText(ByVal rawText As String) As Boolean
    IsExplicitLanceMapText = _
        InStr(1, rawText, "=", vbTextCompare) > 0 Or _
        InStr(1, rawText, ":", vbTextCompare) > 0 Or _
        InStr(1, rawText, "->", vbTextCompare) > 0
End Function

Private Function BuildLanceLevelListFromMap(ByVal mapText As String) As String
    Dim parts() As String
    Dim i As Long
    Dim chunk As String
    Dim sepPos As Long
    Dim levelText As String
    Dim lanceText As String

    If Trim$(mapText) = "" Then Exit Function

    parts = Split(mapText, ";")
    For i = LBound(parts) To UBound(parts)
        chunk = Trim$(parts(i))
        If chunk = "" Then GoTo NextItem

        sepPos = InStr(1, chunk, "=", vbTextCompare)
        If sepPos <= 1 Or sepPos >= Len(chunk) Then GoTo NextItem

        levelText = Trim$(Left$(chunk, sepPos - 1))
        lanceText = Trim$(Mid$(chunk, sepPos + 1))
        If Left$(levelText, 1) <> "+" Then levelText = "+" & levelText

        If BuildLanceLevelListFromMap <> "" Then BuildLanceLevelListFromMap = BuildLanceLevelListFromMap & "; "
        BuildLanceLevelListFromMap = BuildLanceLevelListFromMap & lanceText & ":" & levelText
NextItem:
    Next i
End Function

Private Function BuildLanceMapFromLists(ByVal levelsCsv As String, ByVal lancesCsv As String) As String
    Dim levelParts() As String
    Dim lanceParts() As String
    Dim i As Long
    Dim levelCount As Long
    Dim lanceCount As Long
    Dim token As String
    Dim rawText As String

    rawText = Trim$(lancesCsv)
    If IsExplicitLanceMapText(rawText) Then
        BuildLanceMapFromLists = BuildExplicitLanceMap(rawText)
        Exit Function
    End If

    lancesCsv = Replace(lancesCsv, ";", ",")
    lancesCsv = Replace(lancesCsv, vbCrLf, ",")
    lancesCsv = Replace(lancesCsv, vbCr, ",")
    lancesCsv = Replace(lancesCsv, vbLf, ",")

    If Trim$(levelsCsv) = "" Or Trim$(lancesCsv) = "" Then Exit Function

    levelParts = Split(levelsCsv, ",")
    lanceParts = Split(lancesCsv, ",")
    levelCount = UBound(levelParts) - LBound(levelParts) + 1
    lanceCount = UBound(lanceParts) - LBound(lanceParts) + 1

    Do While lanceCount > 0 And Trim$(lanceParts(lanceCount - 1)) = ""
        lanceCount = lanceCount - 1
    Loop

    If lanceCount > levelCount Then Exit Function

    For i = 0 To lanceCount - 1
        token = Trim$(lanceParts(i))
        If token = "" Then GoTo NextItem
        If Not IsNumeric(token) Then Exit Function
        If CLng(Val(token)) = 0 Then GoTo NextItem

        If BuildLanceMapFromLists <> "" Then BuildLanceMapFromLists = BuildLanceMapFromLists & ";"
        BuildLanceMapFromLists = BuildLanceMapFromLists & Trim$(levelParts(i)) & "=" & CLng(token)
NextItem:
    Next i
End Function

Private Function GetSuggestedArmpilLances(ByVal levelsCsv As String, Optional ByVal knownLancesCsv As String = "") As String
    Dim raw As String
    Dim parts() As String
    Dim startIndex As Long
    Dim partCount As Long
    Dim blankCount As Long
    Dim pos As Long
    Dim i As Long
    Dim levelCount As Long

    levelCount = CountCsvItems(levelsCsv)
    If levelCount <= 0 Then Exit Function

    raw = Trim$(knownLancesCsv)
    If raw = "" Then raw = GetKnownLancesForPython()
    If raw = "" Then
        GetSuggestedArmpilLances = BuildFallbackArmpilLancesFromLevels(levelsCsv)
        Exit Function
    End If

    parts = Split(raw, ",")
    partCount = UBound(parts) - LBound(parts) + 1

    If partCount > levelCount Then
        startIndex = UBound(parts) - levelCount + 1
        partCount = levelCount
        blankCount = 0
    Else
        startIndex = LBound(parts)
        blankCount = levelCount - partCount
    End If

    For pos = 1 To levelCount
        If pos > 1 Then GetSuggestedArmpilLances = GetSuggestedArmpilLances & ","
        If pos > blankCount Then
            i = startIndex + pos - blankCount - 1
            GetSuggestedArmpilLances = GetSuggestedArmpilLances & Trim$(parts(i))
        End If
    Next pos
End Function

Private Function BuildFallbackArmpilLancesFromLevels(ByVal levelsCsv As String) As String
    Dim levelParts() As String
    Dim lanceValues() As Long
    Dim hasValue() As Boolean
    Dim levelCount As Long
    Dim i As Long
    Dim anchorIndex As Long
    Dim currentLance As Long
    Dim defaultLance As Long

    If Trim$(levelsCsv) = "" Then Exit Function

    levelParts = Split(levelsCsv, ",")
    levelCount = UBound(levelParts) - LBound(levelParts) + 1
    If levelCount <= 0 Then Exit Function

    ReDim lanceValues(0 To levelCount - 1)
    ReDim hasValue(0 To levelCount - 1)

    anchorIndex = -1
    For i = 0 To levelCount - 1
        If TryGetDefaultArmpilLanceForLevel(levelParts(i), defaultLance) Then
            lanceValues(i) = defaultLance
            hasValue(i) = True
            If anchorIndex = -1 And defaultLance > 0 Then anchorIndex = i
        End If
    Next i

    If anchorIndex = -1 Then Exit Function

    currentLance = lanceValues(anchorIndex)
    For i = anchorIndex - 1 To 0 Step -1
        If hasValue(i) Then
            If lanceValues(i) > 0 Then currentLance = lanceValues(i)
        Else
            currentLance = currentLance - 1
            If currentLance > 0 Then
                lanceValues(i) = currentLance
                hasValue(i) = True
            End If
        End If
    Next i

    currentLance = lanceValues(anchorIndex)
    For i = anchorIndex + 1 To levelCount - 1
        If hasValue(i) Then
            If lanceValues(i) > 0 Then currentLance = lanceValues(i)
        Else
            currentLance = currentLance + 1
            lanceValues(i) = currentLance
            hasValue(i) = True
        End If
    Next i

    For i = 0 To levelCount - 1
        If i > 0 Then BuildFallbackArmpilLancesFromLevels = BuildFallbackArmpilLancesFromLevels & ","
        If hasValue(i) Then BuildFallbackArmpilLancesFromLevels = BuildFallbackArmpilLancesFromLevels & CStr(lanceValues(i))
    Next i
End Function

Private Function TryGetDefaultArmpilLanceForLevel(ByVal levelText As String, ByRef lanceValue As Long) As Boolean
    Dim normalizedLevel As String
    Dim levelValue As Double

    normalizedLevel = NormalizeLevelToken(levelText)
    levelValue = Val(normalizedLevel)
    If levelValue <= 0# Then Exit Function

    If Abs(levelValue - 1040.25) < 0.01 Then
        lanceValue = 0
        TryGetDefaultArmpilLanceForLevel = True
    ElseIf Abs(levelValue - 1043.4) < 0.01 Then
        lanceValue = 6
        TryGetDefaultArmpilLanceForLevel = True
    ElseIf Abs(levelValue - 1046.6) < 0.01 Then
        lanceValue = 7
        TryGetDefaultArmpilLanceForLevel = True
    End If
End Function

Private Function CountCsvItems(ByVal csvText As String) As Long
    If Trim$(csvText) = "" Then Exit Function
    CountCsvItems = UBound(Split(csvText, ",")) + 1
End Function

Private Function FormatLevelsForPrompt(ByVal levelsCsv As String) As String
    Dim parts() As String
    Dim i As Long

    If Trim$(levelsCsv) = "" Then Exit Function

    parts = Split(levelsCsv, ",")
    For i = 0 To UBound(parts)
        If FormatLevelsForPrompt <> "" Then FormatLevelsForPrompt = FormatLevelsForPrompt & ", "
        FormatLevelsForPrompt = FormatLevelsForPrompt & "+" & Trim$(parts(i))
    Next i
End Function

Private Function BuildArmpilLevelsPrompt(ByVal allLevelsCsv As String, ByVal mappedLevelsCsv As String) As String
    BuildArmpilLevelsPrompt = "Todos os niveis detectados no PDF:" & vbCrLf & _
        "  " & FormatLevelsForPrompt(allLevelsCsv)

    If Trim$(mappedLevelsCsv) <> "" And Trim$(allLevelsCsv) <> Trim$(mappedLevelsCsv) Then
        BuildArmpilLevelsPrompt = BuildArmpilLevelsPrompt & vbCrLf & vbCrLf & _
            "Niveis com armadura para mapear:" & vbCrLf & _
            "  " & FormatLevelsForPrompt(mappedLevelsCsv)
    End If
End Function

Private Function BuildArmpilManualPrompt(ByVal allLevelsCsv As String, ByVal identifiedLevelsCsv As String, ByVal defaultPairs As String) As String
    If Trim$(identifiedLevelsCsv) <> "" And Trim$(identifiedLevelsCsv) <> Trim$(allLevelsCsv) Then
        BuildArmpilManualPrompt = _
            "Todos os niveis detectados no PDF (inclui niveis ignorados pelo script):" & vbCrLf & _
            "  " & FormatLevelsForPrompt(allLevelsCsv) & vbCrLf & vbCrLf
    Else
        BuildArmpilManualPrompt = _
            "Niveis detectados no PDF:" & vbCrLf & _
            "  " & FormatLevelsForPrompt(allLevelsCsv) & vbCrLf & vbCrLf
    End If

    BuildArmpilManualPrompt = BuildArmpilManualPrompt & _
        "Digite somente os lances na mesma ordem, separados por virgula." & vbCrLf & _
        "Deixe em branco ou use 0 para ignorar um nivel." & vbCrLf & _
        "Ex.: 0,6,7,8" & vbCrLf & vbCrLf & _
        "Se preferir, use pares lance:nivel." & vbCrLf & _
        "Ex.: " & IIf(Trim$(defaultPairs) <> "", defaultPairs, "6:+1043.40; 7:+1046.60")
End Function

Private Function BuildArmpilMapErrorMessage(ByVal defaultPairs As String) As String
    BuildArmpilMapErrorMessage = _
        "Entrada invalida." & vbCrLf & vbCrLf & _
        "Use uma destas opcoes:" & vbCrLf & _
        "1. Somente os lances na ordem dos niveis, separados por virgula." & vbCrLf & _
        "   Deixe em branco ou use 0 para ignorar. Ex.: 0,6,7,8" & vbCrLf & vbCrLf & _
        "2. Pares no formato lance:nivel." & vbCrLf & _
        "   Ex.: " & IIf(Trim$(defaultPairs) <> "", defaultPairs, "6:+1043.40; 7:+1046.60")
End Function

Private Function BuildLanceEntriesForLevels(ByVal levelsCsv As String, ByVal mapText As String) As String
    Dim dict As Object
    Set dict = CreateObject("Scripting.Dictionary")

    Dim parts() As String
    Dim i As Long
    Dim chunk As String
    Dim sepPos As Long
    Dim levelText As String
    Dim lanceText As String
    Dim levelParts() As String
    Dim normalizedLevel As String

    If Trim$(levelsCsv) = "" Or Trim$(mapText) = "" Then Exit Function

    parts = Split(mapText, ";")
    For i = LBound(parts) To UBound(parts)
        chunk = Trim$(parts(i))
        If chunk = "" Then GoTo NextMapItem

        sepPos = InStr(1, chunk, "=", vbTextCompare)
        If sepPos <= 1 Or sepPos >= Len(chunk) Then GoTo NextMapItem

        levelText = Trim$(Left$(chunk, sepPos - 1))
        lanceText = Trim$(Mid$(chunk, sepPos + 1))
        normalizedLevel = NormalizeLevelToken(levelText)
        If normalizedLevel <> "" And lanceText <> "" Then dict(normalizedLevel) = lanceText
NextMapItem:
    Next i

    levelParts = Split(levelsCsv, ",")
    For i = LBound(levelParts) To UBound(levelParts)
        If i > LBound(levelParts) Then BuildLanceEntriesForLevels = BuildLanceEntriesForLevels & ","
        normalizedLevel = NormalizeLevelToken(levelParts(i))
        If dict.Exists(normalizedLevel) Then
            BuildLanceEntriesForLevels = BuildLanceEntriesForLevels & CStr(dict(normalizedLevel))
        End If
    Next i
End Function

Private Function NormalizeLevelToken(ByVal levelText As String) As String
    levelText = Trim$(levelText)
    If Left$(levelText, 1) = "+" Then levelText = Mid$(levelText, 2)
    levelText = Replace(levelText, ",", ".")
    NormalizeLevelToken = levelText
End Function

Private Function PickArmpilPdfPath() As String
    Dim fd As FileDialog
    Set fd = Application.FileDialog(msoFileDialogFilePicker)

    fd.Title = "Selecione o PDF ARMPIL"
    fd.Filters.Clear
    fd.Filters.Add "PDF", "*.pdf"
    fd.Filters.Add "Todos", "*.*"
    fd.AllowMultiSelect = False

    If fd.Show <> -1 Then Exit Function
    PickArmpilPdfPath = fd.SelectedItems(1)
End Function

Private Function GetArmpilScriptPath() As String
    Dim sep As String
    sep = Application.PathSeparator

    Dim candidates(2) As String
    candidates(0) = ThisWorkbook.Path & sep & "armpil_extractor.py"
    candidates(1) = ThisWorkbook.Path & sep & ".." & sep & "src" & sep & "armpil_extractor.py"
    candidates(2) = ThisWorkbook.Path & sep & "src" & sep & "armpil_extractor.py"

    Dim i As Long
    For i = 0 To UBound(candidates)
        If Dir$(candidates(i)) <> "" Then
            GetArmpilScriptPath = candidates(i)
            Exit Function
        End If
    Next i

    Err.Raise vbObjectError + 2004, , _
        "Arquivo armpil_extractor.py não encontrado." & vbCrLf & _
        "Locais verificados:" & vbCrLf & _
        candidates(0) & vbCrLf & _
        candidates(1) & vbCrLf & _
        candidates(2)
End Function

Private Function GetPythonCommand(ByRef exeName As String, ByRef exeArgs As String) As Boolean
    Dim candidates As Variant
    Dim candidate As Variant

    candidates = Array( _
        Array("python", ""), _
        Array("py", "-3"), _
        Array("python3", "") _
    )

    For Each candidate In candidates
        If CanRunPythonInterpreter(CStr(candidate(0)), Trim$(CStr(candidate(1)))) Then
            exeName = CStr(candidate(0))
            exeArgs = Trim$(CStr(candidate(1)))
            GetPythonCommand = True
            Exit Function
        End If
    Next candidate
End Function

Private Function CanRunPythonInterpreter(ByVal exeName As String, ByVal exeArgs As String) As Boolean
    Dim shellObj As Object
    Dim launcherFile As String
    Dim exitCode As Long

    Set shellObj = CreateObject("WScript.Shell")
    launcherFile = Environ$("TEMP") & Application.PathSeparator & "armpil_check_" & Replace(exeName, ".", "_") & ".cmd"

    WriteTextFile launcherFile, BuildPythonCheckScript(exeName, exeArgs)
    exitCode = shellObj.Run("cmd.exe /d /c " & QuotePath(launcherFile), 0, True)
    If Dir$(launcherFile) <> "" Then Kill launcherFile

    CanRunPythonInterpreter = (exitCode = 0)
End Function

Private Function QuotePath(ByVal path As String) As String
    QuotePath = Chr$(34) & path & Chr$(34)
End Function

Private Function BuildExecutableCommand(ByVal exeName As String, ByVal args As String) As String
    Dim cmd As String

    cmd = QuotePath(exeName)
    If Trim$(args) <> "" Then
        cmd = cmd & " " & Trim$(args)
    End If

    BuildExecutableCommand = cmd
End Function

Private Function BuildPythonLauncherScript(ByVal exeName As String, ByVal exeArgs As String, ByVal scriptPath As String, ByVal resultFile As String, ByVal pdfPath As String, Optional ByVal lanceMap As String = "", Optional ByVal extraArgs As String = "") As String
    Dim lines As String

    lines = "@echo off" & vbCrLf
    lines = lines & "setlocal" & vbCrLf
    lines = lines & "set ""ARMPIL_RESULT_FILE=" & resultFile & """" & vbCrLf
    lines = lines & "set ""ARMPIL_OUTPUT_DIR=" & GetArmpilOutputDir() & """" & vbCrLf
    lines = lines & "set ""ARMPIL_PDF_PATH=" & pdfPath & """" & vbCrLf
    lines = lines & "set ""ARMPIL_KNOWN_LANCES=" & GetKnownLancesForPython() & """" & vbCrLf
    If Trim$(lanceMap) <> "" Then
        lines = lines & "set ""ARMPIL_LANCE_MAP=" & lanceMap & """" & vbCrLf
    End If
    lines = lines & BuildExecutableCommand(exeName, exeArgs) & " " & QuotePath(scriptPath)
    If Trim$(extraArgs) <> "" Then
        lines = lines & " " & Trim$(extraArgs)
    End If
    lines = lines & vbCrLf
    lines = lines & "exit /b %errorlevel%" & vbCrLf

    BuildPythonLauncherScript = lines
End Function

Private Function BuildPythonCheckScript(ByVal exeName As String, ByVal exeArgs As String) As String
    Dim lines As String

    lines = "@echo off" & vbCrLf
    lines = lines & BuildExecutableCommand(exeName, exeArgs) & " -c ""import sys, fitz; exit(0 if getattr(sys, '_is_gil_enabled', lambda: True)() else 1)""" & vbCrLf
    lines = lines & "exit /b %errorlevel%" & vbCrLf

    BuildPythonCheckScript = lines
End Function

Private Function GetArmpilOutputDir() As String
    Dim publicDir As String
    publicDir = Environ$("PUBLIC")

    If publicDir <> "" Then
        GetArmpilOutputDir = publicDir & Application.PathSeparator & "Documents" & _
            Application.PathSeparator & "Scripts Formula" & Application.PathSeparator & "ARMPIL"
    Else
        GetArmpilOutputDir = Environ$("TEMP")
    End If
End Function

Private Function ExtractTaggedValue(ByVal text As String, ByVal tag As String) As String
    Dim normalized As String
    Dim lines() As String
    Dim i As Long
    Dim line As String

    normalized = Replace(text, vbCrLf, vbLf)
    normalized = Replace(normalized, vbCr, vbLf)
    lines = Split(normalized, vbLf)

    For i = LBound(lines) To UBound(lines)
        line = Trim$(lines(i))
        If Left$(line, Len(tag)) = tag Then
            ExtractTaggedValue = Trim$(Mid$(line, Len(tag) + 1))
            Exit Function
        End If
    Next i
End Function

Private Function BuildPythonErrorMessage(ByVal stdoutText As String, ByVal stderrText As String) As String
    Dim msg As String

    msg = Trim$(stdoutText)
    If msg = "" Then msg = "Falha ao executar o script Python." & vbCrLf & vbCrLf & "Comando:" & vbCrLf & stderrText

    BuildPythonErrorMessage = msg
End Function

Private Function ReadTextFileSafe(ByVal path As String) As String
    Dim ff As Integer

    If Dir$(path) = "" Then Exit Function

    ff = FreeFile
    Open path For Input As #ff
    ReadTextFileSafe = Input$(LOF(ff), #ff)
    Close #ff
End Function

Private Function FileExists(ByVal path As String) As Boolean
    On Error GoTo Fallback
    FileExists = CreateObject("Scripting.FileSystemObject").FileExists(path)
    Exit Function

Fallback:
    FileExists = (Dir$(path) <> "")
End Function

Private Sub WriteTextFile(ByVal path As String, ByVal content As String)
    Dim ff As Integer

    ff = FreeFile
    Open path For Output As #ff
    Print #ff, content;
    Close #ff
End Sub

' ================================================================
' HELPERS DE LEITURA
' ================================================================
Private Function ReadAllNonEmptyLines(ByVal path As String) As Variant
    Dim ff As Integer
    ff = FreeFile
    
    Dim fileContent As String
    Open path For Binary Access Read As #ff
    fileContent = Space$(LOF(ff))
    Get #ff, , fileContent
    Close #ff

    ' Remove BOM UTF-8
    If Len(fileContent) >= 3 Then
        If Asc(Mid$(fileContent, 1, 1)) = 239 And _
           Asc(Mid$(fileContent, 2, 1)) = 187 And _
           Asc(Mid$(fileContent, 3, 1)) = 191 Then
            fileContent = Mid$(fileContent, 4)
        End If
    End If

    fileContent = Replace(fileContent, vbCrLf, vbLf)
    fileContent = Replace(fileContent, vbCr, vbLf)

    Dim rawLines() As String
    rawLines = Split(fileContent, vbLf)

    Dim tmp() As String
    ReDim tmp(0 To UBound(rawLines))

    Dim count As Long
    count = 0

    Dim i As Long
    Dim s As String
    For i = LBound(rawLines) To UBound(rawLines)
        s = Trim$(rawLines(i))
        If s <> "" Then
            tmp(count) = s
            count = count + 1
        End If
    Next i

    If count = 0 Then
        ReadAllNonEmptyLines = Array()
        Exit Function
    End If

    Dim result() As String
    ReDim result(0 To count - 1)

    For i = 0 To count - 1
        result(i) = tmp(i)
    Next i

    ReadAllNonEmptyLines = result
End Function

Private Function ExtractSelePilarName(ByVal line As String) As String
    Dim raw As String
    Dim sp As Long
    Dim par As Long

    raw = Trim$(Mid$(line, 7))
    sp = InStr(raw, " ")
    If sp > 0 Then raw = Left$(raw, sp - 1)
    par = InStr(raw, "(")
    If par > 0 Then raw = Left$(raw, par - 1)

    ExtractSelePilarName = NormalizePilarName(raw)
End Function

Private Function ExtractSeleLanceTitle(ByVal line As String) As String
    Dim s As String
    Dim rest As String
    Dim sp As Long
    Dim i As Long

    s = LTrim$(line)
    sp = InStr(s, " ")
    If sp = 0 Then Exit Function

    rest = LTrim$(Mid$(s, sp + 1))
    For i = 1 To Len(rest) - 1
        If Mid$(rest, i, 2) = "  " Then
            ExtractSeleLanceTitle = Trim$(Left$(rest, i - 1))
            Exit Function
        End If
    Next i

    ExtractSeleLanceTitle = Trim$(Left$(rest, 16))
End Function

Private Function NormalizePilarName(ByVal raw As String) As String
    NormalizePilarName = UCase$(Trim$(raw))
End Function

Private Function BuildPilarKey(ByVal pilar As String, ByVal lanceValue As Variant) As String
    BuildPilarKey = NormalizePilarName(pilar) & "|" & Trim$(CStr(lanceValue))
End Function

Private Sub SortNumericVariantArray(ByRef values As Variant)
    Dim i As Long
    Dim j As Long
    Dim tmp As Variant

    If Not IsArray(values) Then Exit Sub
    If UBound(values) <= LBound(values) Then Exit Sub

    For i = LBound(values) To UBound(values) - 1
        For j = i + 1 To UBound(values)
            If CLng(values(i)) > CLng(values(j)) Then
                tmp = values(i)
                values(i) = values(j)
                values(j) = tmp
            End If
        Next j
    Next i
End Sub

Private Function JoinVariantList(ByVal values As Variant) As String
    Dim i As Long

    If Not IsArray(values) Then Exit Function

    For i = LBound(values) To UBound(values)
        JoinVariantList = JoinVariantList & CStr(values(i)) & ", "
    Next i

    If Len(JoinVariantList) >= 2 Then
        JoinVariantList = Left$(JoinVariantList, Len(JoinVariantList) - 2)
    End If
End Function

Private Function CompactPromptText(ByVal text As String, ByVal maxLen As Long) As String
    text = Trim$(text)
    If maxLen <= 0 Or Len(text) <= maxLen Then
        CompactPromptText = text
    Else
        CompactPromptText = Left$(text, maxLen - 4) & " ..."
    End If
End Function

Private Function BuildPromptListText(ByVal detailedText As String, ByVal fallbackText As String, ByVal maxLen As Long) As String
    If Trim$(detailedText) <> "" Then
        BuildPromptListText = CompactPromptText(detailedText, maxLen)
    Else
        BuildPromptListText = CompactPromptText(fallbackText, maxLen)
    End If
End Function

Private Function BuildLanceTitleList(ByVal values As Variant, ByVal titles As Object) As String
    Dim i As Long
    Dim lanceValue As Long
    Dim itemText As String

    If Not IsArray(values) Then Exit Function

    For i = LBound(values) To UBound(values)
        lanceValue = CLng(values(i))
        itemText = CStr(lanceValue)
        If Not titles Is Nothing Then
            If titles.Exists(lanceValue) Then itemText = itemText & ":" & CStr(titles(lanceValue))
        End If

        If BuildLanceTitleList <> "" Then BuildLanceTitleList = BuildLanceTitleList & "; "
        BuildLanceTitleList = BuildLanceTitleList & itemText
    Next i
End Function

Private Function BuildLanceTitleListFromCsv(ByVal lanceCsv As String, ByVal titles As Object) As String
    Dim parts() As String
    Dim i As Long
    Dim token As String
    Dim itemText As String
    Dim lanceValue As Long

    lanceCsv = Replace(lanceCsv, ";", ",")
    If Trim$(lanceCsv) = "" Then Exit Function

    parts = Split(lanceCsv, ",")
    For i = LBound(parts) To UBound(parts)
        token = Trim$(parts(i))
        If token = "" Then GoTo NextItem
        If Not IsNumeric(token) Then GoTo NextItem

        lanceValue = CLng(token)
        itemText = CStr(lanceValue)
        If Not titles Is Nothing Then
            If titles.Exists(lanceValue) Then itemText = itemText & ":" & CStr(titles(lanceValue))
        End If

        If BuildLanceTitleListFromCsv <> "" Then BuildLanceTitleListFromCsv = BuildLanceTitleListFromCsv & "; "
        BuildLanceTitleListFromCsv = BuildLanceTitleListFromCsv & itemText
NextItem:
    Next i
End Function

Private Function BuildPromptLanceList(ByVal values As Variant, ByVal titles As Object) As String
    Dim i As Long
    Dim lanceValue As Long

    If Not IsArray(values) Then Exit Function

    For i = LBound(values) To UBound(values)
        lanceValue = CLng(values(i))
        If BuildPromptLanceList <> "" Then BuildPromptLanceList = BuildPromptLanceList & vbCrLf
        BuildPromptLanceList = BuildPromptLanceList & BuildPromptLanceItem(lanceValue, titles)
    Next i
End Function

Private Function BuildPromptLanceListFromCsv(ByVal lanceCsv As String, ByVal titles As Object) As String
    Dim parts() As String
    Dim i As Long
    Dim token As String

    lanceCsv = Replace(lanceCsv, ";", ",")
    If Trim$(lanceCsv) = "" Then Exit Function

    parts = Split(lanceCsv, ",")
    For i = LBound(parts) To UBound(parts)
        token = Trim$(parts(i))
        If token = "" Then GoTo NextPromptItem
        If Not IsNumeric(token) Then GoTo NextPromptItem

        If BuildPromptLanceListFromCsv <> "" Then BuildPromptLanceListFromCsv = BuildPromptLanceListFromCsv & vbCrLf
        BuildPromptLanceListFromCsv = BuildPromptLanceListFromCsv & BuildPromptLanceItem(CLng(token), titles)
NextPromptItem:
    Next i
End Function

Private Function BuildPromptLanceItem(ByVal lanceValue As Long, ByVal titles As Object) As String
    BuildPromptLanceItem = "[LANCE " & CStr(lanceValue) & "]"
    If Not titles Is Nothing Then
        If titles.Exists(lanceValue) Then BuildPromptLanceItem = BuildPromptLanceItem & "  " & CStr(titles(lanceValue))
    End If
End Function

Private Function GetSheetLancesDict(ByVal ws As Worksheet, ByVal rowStart As Long, ByVal colLance As Long) As Object
    Dim dict As Object
    Set dict = CreateObject("Scripting.Dictionary")

    Dim lastRow As Long
    lastRow = ws.Cells(ws.Rows.count, colLance).End(xlUp).Row
    If lastRow < rowStart Then
        Set GetSheetLancesDict = dict
        Exit Function
    End If

    Dim data As Variant
    data = ws.Range(ws.Cells(rowStart, colLance), ws.Cells(lastRow, colLance)).Value2

    Dim i As Long
    If IsArray(data) Then
        For i = 1 To UBound(data, 1)
            AddNumericLanceToDict dict, data(i, 1)
        Next i
    Else
        AddNumericLanceToDict dict, data
    End If

    Set GetSheetLancesDict = dict
End Function

Private Sub AddNumericLanceToDict(ByRef dict As Object, ByVal value As Variant)
    Dim text As String

    If IsError(value) Then Exit Sub
    If IsNull(value) Then Exit Sub
    If IsEmpty(value) Then Exit Sub
    text = Trim$(CStr(value))
    If text = "" Then Exit Sub
    If Not IsNumeric(text) Then Exit Sub

    dict(CLng(text)) = True
End Sub

Private Function GetKnownLancesForPython() As String
    Dim dict As Object
    Set dict = GetSheetLancesDict(ThisWorkbook.Sheets("SELE"), 6, 3)
    If dict.count = 0 Then Exit Function

    Dim keys As Variant
    keys = dict.keys
    SortNumericVariantArray keys
    GetKnownLancesForPython = JoinVariantList(keys)
End Function

Private Function BuildSuggestedSeleLances(ByVal availableLances As Variant) As String
    Dim dict As Object
    Set dict = GetSheetLancesDict(ThisWorkbook.Sheets("ARMPIL"), 6, 3)
    If dict.count = 0 Then Exit Function

    Dim matches As Object
    Set matches = CreateObject("Scripting.Dictionary")

    Dim i As Long
    For i = LBound(availableLances) To UBound(availableLances)
        If dict.Exists(CLng(availableLances(i))) Then
            matches(CLng(availableLances(i))) = True
        End If
    Next i

    If matches.count = 0 Then Exit Function

    Dim keys As Variant
    keys = matches.keys
    SortNumericVariantArray keys
    BuildSuggestedSeleLances = JoinVariantList(keys)
End Function

Private Function BuildLanceFilterSet(ByVal rawText As String) As Object
    Dim dict As Object
    Set dict = CreateObject("Scripting.Dictionary")

    Dim cleaned As String
    cleaned = Trim$(rawText)
    If cleaned = "" Then
        Set BuildLanceFilterSet = dict
        Exit Function
    End If

    Dim parts() As String
    parts = Split(cleaned, ",")

    Dim i As Long
    For i = 0 To UBound(parts)
        Dim token As String
        token = Trim$(parts(i))
        If IsNumeric(token) Then
            dict(CLng(token)) = True
        End If
    Next i

    Set BuildLanceFilterSet = dict
End Function

Private Function PromptSeleLanceFilter(ByVal availableList As String, ByVal suggestedList As String, Optional ByVal availableDetails As String = "", Optional ByVal suggestedDetails As String = "") As Variant
    Dim choice As VbMsgBoxResult
    Dim availableDisplay As String
    Dim suggestedDisplay As String

    availableDisplay = Trim$(availableDetails)
    If availableDisplay = "" Then availableDisplay = availableList
    suggestedDisplay = Trim$(suggestedDetails)
    If suggestedDisplay = "" Then suggestedDisplay = suggestedList

    If suggestedList <> "" And suggestedList <> availableList Then
        choice = MsgBox( _
            "Lances encontrados no SELE:" & vbCrLf & _
            availableDisplay & vbCrLf & vbCrLf & _
            "Lances que ja existem no ARMPIL carregado:" & vbCrLf & _
            suggestedDisplay & vbCrLf & vbCrLf & _
            "Sim = usar a sugestao do ARMPIL" & vbCrLf & _
            "Nao = escolher manualmente" & vbCrLf & _
            "Cancelar = importar todos os lances", _
            vbQuestion + vbYesNoCancel, _
            "Selecionar niveis" _
        )

        If choice = vbYes Then
            PromptSeleLanceFilter = suggestedList
            Exit Function
        End If

        If choice = vbCancel Then
            PromptSeleLanceFilter = ""
            Exit Function
        End If
    End If

    Dim dlgMsg As String
    Dim resp As Variant
    Dim filterSet As Object

    dlgMsg = "Lances detectados no arquivo:" & vbCrLf & _
             availableDisplay & vbCrLf & vbCrLf & _
             "Informe os lances a importar (separados por virgula)." & vbCrLf & _
             "Deixe em branco para importar todos."

    Do
        resp = Application.InputBox(dlgMsg, "Selecionar Niveis", IIf(suggestedList <> "", suggestedList, availableList), Type:=2)
        If IsDialogCancelled(resp) Then
            PromptSeleLanceFilter = False
            Exit Function
        End If

        Set filterSet = BuildLanceFilterSet(Trim$(CStr(resp)))
        If Trim$(CStr(resp)) = "" Or filterSet.count > 0 Then
            PromptSeleLanceFilter = Trim$(CStr(resp))
            Exit Function
        End If

        MsgBox "Nenhum lance valido foi informado. Tente novamente.", vbExclamation
    Loop
End Function

Private Function DetectDelim(ByVal firstLine As String) As String
    If InStr(firstLine, ";") > 0 Then
        DetectDelim = ";"
    Else
        DetectDelim = ","
    End If
End Function

Private Function CleanCSV(ByVal s As String) As String
    s = Trim$(s)
    If Len(s) >= 2 Then
        If Left$(s, 1) = Chr$(34) And Right$(s, 1) = Chr$(34) Then
            s = Mid$(s, 2, Len(s) - 2)
        End If
    End If
    CleanCSV = Replace(Trim$(s), ",", ".")
End Function

Private Function IsDataLine(ByVal line As String) As Boolean
    Dim s As String
    s = LTrim$(line)

    If Len(s) = 0 Then
        IsDataLine = False
        Exit Function
    End If

    Dim first As String
    first = Left$(s, InStr(s & " ", " ") - 1)
    IsDataLine = IsNumeric(first)
End Function

Private Function ParseSeleLine(ByVal line As String, ByRef lance As Long, ByRef asVal As Double) As Boolean
    ParseSeleLine = False

    Dim s As String
    s = line

    Do While InStr(s, "  ") > 0
        s = Replace(s, "  ", " ")
    Loop

    s = Trim$(s)

    Dim parts() As String
    parts = Split(s, " ")

    If UBound(parts) < 8 Then Exit Function
    If Not IsNumeric(parts(0)) Then Exit Function

    lance = CLng(parts(0))

    Dim i As Long
    For i = 4 To UBound(parts) - 2
        Dim p1 As String, p2 As String
        p1 = UCase$(Trim$(parts(i)))
        p2 = UCase$(Trim$(parts(i + 1)))

        If (p1 = "N" Or p1 = "S") And (p2 = "N" Or p2 = "S") Then
            If i + 2 <= UBound(parts) Then
                If IsNumeric(parts(i + 2)) Then
                    asVal = CDbl(parts(i + 2))
                    ParseSeleLine = True
                    Exit Function
                End If
            End If
        End If
    Next i
End Function

Private Sub AddKeysFromData(ByRef dict As Object, ByVal data As Variant)
    Dim i As Long
    Dim pilar As String
    Dim lanceTxt As String
    Dim chave As String

    If Not IsArray(data) Then Exit Sub

    For i = 1 To UBound(data, 1)
        pilar = NormalizePilarName(CStr(data(i, 1)))
        lanceTxt = Trim$(CStr(data(i, 2)))
        If pilar <> "" And lanceTxt <> "" Then
            chave = BuildPilarKey(pilar, lanceTxt)
            If Not dict.Exists(chave) Then dict.Add chave, Array(pilar, data(i, 2))
        End If
    Next i
End Sub

Private Function PromptPilarInput(ByVal ws As Worksheet, ByVal preferredPrefix As String) As String
    Dim resp As Variant
    Dim normalizedPilar As String
    Dim defaultValue As String

    defaultValue = GetSuggestedNextPilarInput(ws)

    Do
        resp = Application.InputBox( _
            "Informe o numero do pilar." & vbCrLf & _
            "O prefixo " & preferredPrefix & " sera aplicado automaticamente." & vbCrLf & _
            "Ex.: " & preferredPrefix & IIf(defaultValue <> "", defaultValue, "44"), _
            "Adicionar pilar", _
            defaultValue, _
            Type:=2 _
        )

        If IsDialogCancelled(resp) Then Exit Function

        If TryNormalizeManualPilarInput(CStr(resp), preferredPrefix, normalizedPilar) Then
            PromptPilarInput = Trim$(CStr(resp))
            Exit Function
        End If

        MsgBox "Informe somente o numero do pilar, com opcional sufixo. Ex.: 44 ou 48A.", vbExclamation, "Adicionar pilar"
    Loop
End Function

Private Function PromptPositiveLongValue(ByVal promptText As String, ByVal titleText As String, ByVal defaultValue As String, ByRef parsedValue As Long) As Boolean
    Dim resp As Variant

    Do
        resp = Application.InputBox(promptText, titleText, defaultValue, Type:=2)
        If IsDialogCancelled(resp) Then Exit Function

        If TryGetPositiveLong(CStr(resp), parsedValue) Then
            PromptPositiveLongValue = True
            Exit Function
        End If

        MsgBox "Informe um numero inteiro maior que zero.", vbExclamation, titleText
    Loop
End Function

Private Function PromptPositiveDoubleValue(ByVal promptText As String, ByVal titleText As String, ByVal defaultValue As String, ByRef parsedValue As Double) As Boolean
    Dim resp As Variant

    Do
        resp = Application.InputBox(promptText, titleText, defaultValue, Type:=2)
        If IsDialogCancelled(resp) Then Exit Function

        If TryGetPositiveDouble(CStr(resp), parsedValue) Then
            PromptPositiveDoubleValue = True
            Exit Function
        End If

        MsgBox "Informe um numero maior que zero.", vbExclamation, titleText
    Loop
End Function

Private Function GetSuggestedNextPilarInput(ByVal ws As Worksheet) As String
    Dim lastRow As Long
    Dim data As Variant
    Dim i As Long
    Dim maxNumber As Long
    Dim currentNumber As Double

    lastRow = GetLastUsedRowInColumns(ws, 2, 2)
    If lastRow < 6 Then Exit Function

    data = ws.Range(ws.Cells(6, 2), ws.Cells(lastRow, 2)).Value2
    If IsArray(data) Then
        For i = 1 To UBound(data, 1)
            currentNumber = GetPilarSortNumber(CStr(data(i, 1)))
            If currentNumber > 0# And currentNumber < 1000000000# Then
                If CLng(currentNumber) > maxNumber Then maxNumber = CLng(currentNumber)
            End If
        Next i
    Else
        currentNumber = GetPilarSortNumber(CStr(data))
        If currentNumber > 0# And currentNumber < 1000000000# Then maxNumber = CLng(currentNumber)
    End If

    If maxNumber > 0 Then GetSuggestedNextPilarInput = CStr(maxNumber + 1)
End Function

Private Function GetSuggestedLanceForNewPilar(ByVal ws As Worksheet) As String
    Dim lastRow As Long
    Dim cellValue As String

    lastRow = GetLastUsedRowInColumns(ws, 3, 3)
    If lastRow < 6 Then Exit Function

    cellValue = Trim$(CStr(ws.Cells(lastRow, 3).Value2))
    If IsNumeric(cellValue) Then GetSuggestedLanceForNewPilar = cellValue
End Function

Private Function GetPreferredPilarPrefix(ByVal ws As Worksheet) As String
    Dim detectedPrefix As String

    If TryGetPilarPrefixFromSheet(ws, detectedPrefix) Then
        GetPreferredPilarPrefix = detectedPrefix
        Exit Function
    End If

    On Error Resume Next
    If TryGetPilarPrefixFromSheet(ThisWorkbook.Sheets("SELE"), detectedPrefix) Then
        GetPreferredPilarPrefix = detectedPrefix
    Else
        GetPreferredPilarPrefix = "P"
    End If
    On Error GoTo 0
End Function

Private Function TryGetPilarPrefixFromSheet(ByVal ws As Worksheet, ByRef detectedPrefix As String) As Boolean
    Dim lastRow As Long
    Dim data As Variant
    Dim i As Long
    Dim pilarText As String

    lastRow = GetLastUsedRowInColumns(ws, 2, 2)
    If lastRow < 6 Then Exit Function

    data = ws.Range(ws.Cells(6, 2), ws.Cells(lastRow, 2)).Value2

    If IsArray(data) Then
        For i = 1 To UBound(data, 1)
            pilarText = NormalizePilarName(CStr(data(i, 1)))
            If Left$(pilarText, 3) = "PAF" Then
                detectedPrefix = "PAF"
                TryGetPilarPrefixFromSheet = True
                Exit Function
            End If
            If Left$(pilarText, 1) = "P" Then
                detectedPrefix = "P"
                TryGetPilarPrefixFromSheet = True
                Exit Function
            End If
        Next i
    Else
        pilarText = NormalizePilarName(CStr(data))
        If Left$(pilarText, 3) = "PAF" Then
            detectedPrefix = "PAF"
            TryGetPilarPrefixFromSheet = True
        ElseIf Left$(pilarText, 1) = "P" Then
            detectedPrefix = "P"
            TryGetPilarPrefixFromSheet = True
        End If
    End If
End Function

Private Function TryNormalizeManualPilarInput(ByVal rawValue As Variant, ByVal preferredPrefix As String, ByRef normalizedPilar As String) As Boolean
    Dim rawText As String
    Dim pilarBody As String

    rawText = UCase$(Trim$(CStr(rawValue)))
    rawText = Replace(rawText, " ", "")
    If rawText = "" Then Exit Function

    If Left$(rawText, 3) = "PAF" Then
        pilarBody = Mid$(rawText, 4)
    ElseIf Left$(rawText, 1) = "P" Then
        pilarBody = Mid$(rawText, 2)
    Else
        pilarBody = rawText
    End If

    If Not IsSimplePilarBody(pilarBody) Then Exit Function

    normalizedPilar = preferredPrefix & pilarBody
    TryNormalizeManualPilarInput = True
End Function

Private Function IsSimplePilarBody(ByVal pilarBody As String) As Boolean
    Dim i As Long
    Dim ch As String

    pilarBody = Trim$(pilarBody)
    If pilarBody = "" Then Exit Function
    If Not Mid$(pilarBody, 1, 1) Like "#" Then Exit Function

    For i = 1 To Len(pilarBody)
        ch = Mid$(pilarBody, i, 1)
        If Not (ch Like "[A-Z0-9]") Then Exit Function
    Next i

    IsSimplePilarBody = True
End Function

Private Function NormalizeManualArmpilEntries(ByVal ws As Worksheet, ByRef rowCount As Long, ByRef infoMessage As String) As Boolean
    Dim lastRow As Long
    lastRow = GetLastArmpilDataRow(ws)
    If lastRow < 6 Then
        infoMessage = "Nenhuma linha preenchida na ARMPIL para atualizar."
        Exit Function
    End If

    Dim rawData As Variant
    rawData = ws.Range(ws.Cells(6, 2), ws.Cells(lastRow, 5)).Value2

    Dim dataOut() As Variant
    ReDim dataOut(1 To UBound(rawData, 1), 1 To 4)

    Dim pilarValues() As String
    Dim hasLance() As Boolean
    Dim lanceValues() As Long
    Dim qtyValues() As Long
    Dim diamValues() As Double
    Dim sourceRows() As Long
    ReDim pilarValues(1 To UBound(rawData, 1))
    ReDim hasLance(1 To UBound(rawData, 1))
    ReDim lanceValues(1 To UBound(rawData, 1))
    ReDim qtyValues(1 To UBound(rawData, 1))
    ReDim diamValues(1 To UBound(rawData, 1))
    ReDim sourceRows(1 To UBound(rawData, 1))

    Dim issueList As String
    Dim issueCount As Long
    Dim i As Long
    Dim pilarText As String
    Dim lanceValue As Long
    Dim qtyValue As Long
    Dim diamValue As Double
    Dim rowDetail As String
    Dim preferredPrefix As String
    Dim lanceText As String

    rowCount = 0
    preferredPrefix = GetPreferredPilarPrefix(ws)

    For i = 1 To UBound(rawData, 1)
        If IsArmpilInputRowEmpty(rawData(i, 1), rawData(i, 2), rawData(i, 3), rawData(i, 4)) Then
            GoTo NextRow
        End If

        rowDetail = ""
        If Not TryNormalizeManualPilarInput(rawData(i, 1), preferredPrefix, pilarText) Then
            rowDetail = "Pilar invalido"
        ElseIf Not TryGetPositiveLong(rawData(i, 3), qtyValue) Then
            rowDetail = "Qtd(Qf) invalida"
        ElseIf Not TryGetPositiveDouble(rawData(i, 4), diamValue) Then
            rowDetail = "Bitola invalida"
        Else
            lanceText = Trim$(CStr(rawData(i, 2)))
            If lanceText <> "" Then
                If Not TryGetPositiveLong(lanceText, lanceValue) Then
                    rowDetail = "Lance invalido"
                End If
            Else
                lanceValue = 0
            End If
        End If

        If rowDetail <> "" Then
            AppendArmpilValidationIssue issueList, issueCount, i + 5, rowDetail
            GoTo NextRow
        End If

        rowCount = rowCount + 1
        pilarValues(rowCount) = pilarText
        hasLance(rowCount) = (lanceText <> "")
        lanceValues(rowCount) = lanceValue
        qtyValues(rowCount) = qtyValue
        diamValues(rowCount) = diamValue
        sourceRows(rowCount) = i + 5
NextRow:
    Next i

    If issueCount > 0 Then
        infoMessage = _
            "Existem linhas manuais incompletas ou invalidas na ARMPIL:" & vbCrLf & _
            issueList & vbCrLf & vbCrLf & _
            "Preencha numero do Pilar, Qtd(Qf) e Bitola(mm)." & vbCrLf & _
            "O lance pode ficar em branco somente quando a macro conseguir inferi-lo pelo contexto."
        Exit Function
    End If

    If rowCount = 0 Then
        infoMessage = "Nenhuma linha valida encontrada na ARMPIL para atualizar."
        Exit Function
    End If

    If Not ResolveMissingManualLances(pilarValues, hasLance, lanceValues, sourceRows, rowCount, infoMessage) Then
        Exit Function
    End If

    For i = 1 To rowCount
        dataOut(i, 1) = pilarValues(i)
        dataOut(i, 2) = lanceValues(i)
        dataOut(i, 3) = qtyValues(i)
        dataOut(i, 4) = diamValues(i)
    Next i

    ClearARMPIL ws

    ws.Range("B6").Resize(rowCount, 4).Value = dataOut
    ws.Range("F6:F" & 5 + rowCount).FormulaR1C1 = "=RC[-2]*PI()*(RC[-1]^2)/4/100"
    ws.Range("G6:G" & 5 + rowCount).FormulaR1C1 = "=UPPER(TRIM(RC[-5]))&""|""&RC[-4]"
    ws.Range("F6:G" & 5 + rowCount).Calculate

    SortSheetRangeByPilarLance ws, 6, 5 + rowCount, 2, 7, 2, 3, 8
    ws.Range("F6:G" & 5 + rowCount).Calculate

    ws.Range("C6:C" & 5 + rowCount).NumberFormat = "0"
    ws.Range("D6:E" & 5 + rowCount).NumberFormat = "0.00"
    ws.Range("F6:F" & 5 + rowCount).NumberFormat = "0.00"

    ApplyArmpilFormatting ws, 6, 5 + rowCount
    SetArmpilManualHint ws
    ws.Cells(4, 2).Value = "  Atualizado manualmente: " & rowCount & " registros"

    NormalizeManualArmpilEntries = True
End Function

Private Function ResolveMissingManualLances(ByRef pilarValues() As String, ByRef hasLance() As Boolean, ByRef lanceValues() As Long, ByRef sourceRows() As Long, ByVal rowCount As Long, ByRef infoMessage As String) As Boolean
    Dim groupStart As Long
    Dim groupEnd As Long

    groupStart = 1
    Do While groupStart <= rowCount
        groupEnd = groupStart
        Do While groupEnd < rowCount And pilarValues(groupEnd + 1) = pilarValues(groupStart)
            groupEnd = groupEnd + 1
        Loop

        If Not TryResolveManualLanceGroup(pilarValues, hasLance, lanceValues, sourceRows, rowCount, groupStart, groupEnd, infoMessage) Then
            Exit Function
        End If

        groupStart = groupEnd + 1
    Loop

    ResolveMissingManualLances = True
End Function

Private Function TryResolveManualLanceGroup(ByRef pilarValues() As String, ByRef hasLance() As Boolean, ByRef lanceValues() As Long, ByRef sourceRows() As Long, ByVal rowCount As Long, ByVal groupStart As Long, ByVal groupEnd As Long, ByRef infoMessage As String) As Boolean
    Dim i As Long
    Dim hasMissing As Boolean
    Dim prevSeq As String
    Dim nextSeq As String
    Dim candidateSeq As String

    For i = groupStart To groupEnd
        If Not hasLance(i) Then
            hasMissing = True
            Exit For
        End If
    Next i

    If Not hasMissing Then
        TryResolveManualLanceGroup = True
        Exit Function
    End If

    prevSeq = GetNeighborExplicitLanceSequence(pilarValues, hasLance, lanceValues, rowCount, groupStart, groupEnd, -1)
    nextSeq = GetNeighborExplicitLanceSequence(pilarValues, hasLance, lanceValues, rowCount, groupStart, groupEnd, 1)
    candidateSeq = ChooseCandidateLanceSequence(prevSeq, nextSeq, hasLance, lanceValues, groupStart, groupEnd)

    If candidateSeq = "" Then
        infoMessage = BuildMissingLanceMessage(pilarValues(groupStart), sourceRows, groupStart, groupEnd)
        Exit Function
    End If

    ApplyCandidateLanceSequence hasLance, lanceValues, groupStart, groupEnd, candidateSeq
    TryResolveManualLanceGroup = True
End Function

Private Function GetNeighborExplicitLanceSequence(ByRef pilarValues() As String, ByRef hasLance() As Boolean, ByRef lanceValues() As Long, ByVal rowCount As Long, ByVal groupStart As Long, ByVal groupEnd As Long, ByVal direction As Long) As String
    Dim idx As Long
    Dim neighborStart As Long
    Dim neighborEnd As Long

    If direction < 0 Then
        idx = groupStart - 1
        Do While idx >= 1
            neighborEnd = idx
            neighborStart = idx
            Do While neighborStart > 1 And pilarValues(neighborStart - 1) = pilarValues(neighborEnd)
                neighborStart = neighborStart - 1
            Loop

            GetNeighborExplicitLanceSequence = BuildExplicitLanceSequence(hasLance, lanceValues, neighborStart, neighborEnd)
            If GetNeighborExplicitLanceSequence <> "" Then Exit Function

            idx = neighborStart - 1
        Loop
    Else
        idx = groupEnd + 1
        Do While idx <= rowCount
            neighborStart = idx
            neighborEnd = idx
            Do While neighborEnd < rowCount And pilarValues(neighborEnd + 1) = pilarValues(neighborStart)
                neighborEnd = neighborEnd + 1
            Loop

            GetNeighborExplicitLanceSequence = BuildExplicitLanceSequence(hasLance, lanceValues, neighborStart, neighborEnd)
            If GetNeighborExplicitLanceSequence <> "" Then Exit Function

            idx = neighborEnd + 1
        Loop
    End If
End Function

Private Function BuildExplicitLanceSequence(ByRef hasLance() As Boolean, ByRef lanceValues() As Long, ByVal groupStart As Long, ByVal groupEnd As Long) As String
    Dim i As Long

    For i = groupStart To groupEnd
        If Not hasLance(i) Then Exit Function
        If BuildExplicitLanceSequence <> "" Then BuildExplicitLanceSequence = BuildExplicitLanceSequence & ","
        BuildExplicitLanceSequence = BuildExplicitLanceSequence & CStr(lanceValues(i))
    Next i
End Function

Private Function ChooseCandidateLanceSequence(ByVal prevSeq As String, ByVal nextSeq As String, ByRef hasLance() As Boolean, ByRef lanceValues() As Long, ByVal groupStart As Long, ByVal groupEnd As Long) As String
    Dim groupSize As Long
    Dim prevMatches As Boolean
    Dim nextMatches As Boolean
    Dim interSeq As String

    groupSize = groupEnd - groupStart + 1

    If prevSeq <> "" Then
        prevMatches = (CountCsvItems(prevSeq) = groupSize) And DoesCandidateMatchGroup(prevSeq, hasLance, lanceValues, groupStart, groupEnd)
    End If
    If nextSeq <> "" Then
        nextMatches = (CountCsvItems(nextSeq) = groupSize) And DoesCandidateMatchGroup(nextSeq, hasLance, lanceValues, groupStart, groupEnd)
    End If

    If prevMatches And nextMatches Then
        If prevSeq = nextSeq Then
            ChooseCandidateLanceSequence = prevSeq
            Exit Function
        End If
    ElseIf prevMatches Then
        ChooseCandidateLanceSequence = prevSeq
        Exit Function
    ElseIf nextMatches Then
        ChooseCandidateLanceSequence = nextSeq
        Exit Function
    End If

    If prevSeq <> "" And nextSeq <> "" Then
        interSeq = BuildOrderedLanceIntersection(prevSeq, nextSeq)
        If CountCsvItems(interSeq) = groupSize Then
            If DoesCandidateMatchGroup(interSeq, hasLance, lanceValues, groupStart, groupEnd) Then
                ChooseCandidateLanceSequence = interSeq
            End If
        End If
    End If
End Function

Private Function BuildOrderedLanceIntersection(ByVal leftSeq As String, ByVal rightSeq As String) As String
    Dim dict As Object
    Set dict = CreateObject("Scripting.Dictionary")

    Dim seen As Object
    Set seen = CreateObject("Scripting.Dictionary")

    Dim parts() As String
    Dim i As Long
    Dim token As String

    If Trim$(leftSeq) = "" Or Trim$(rightSeq) = "" Then Exit Function

    parts = Split(rightSeq, ",")
    For i = LBound(parts) To UBound(parts)
        token = Trim$(parts(i))
        If token <> "" Then dict(token) = True
    Next i

    parts = Split(leftSeq, ",")
    For i = LBound(parts) To UBound(parts)
        token = Trim$(parts(i))
        If token <> "" Then
            If dict.Exists(token) Then
                If Not seen.Exists(token) Then
                    If BuildOrderedLanceIntersection <> "" Then BuildOrderedLanceIntersection = BuildOrderedLanceIntersection & ","
                    BuildOrderedLanceIntersection = BuildOrderedLanceIntersection & token
                    seen(token) = True
                End If
            End If
        End If
    Next i
End Function

Private Function DoesCandidateMatchGroup(ByVal candidateSeq As String, ByRef hasLance() As Boolean, ByRef lanceValues() As Long, ByVal groupStart As Long, ByVal groupEnd As Long) As Boolean
    Dim parts() As String
    Dim i As Long
    Dim token As String

    If Trim$(candidateSeq) = "" Then Exit Function
    If CountCsvItems(candidateSeq) <> (groupEnd - groupStart + 1) Then Exit Function

    parts = Split(candidateSeq, ",")
    For i = groupStart To groupEnd
        token = Trim$(parts(i - groupStart))
        If Not IsNumeric(token) Then Exit Function
        If hasLance(i) Then
            If CLng(token) <> lanceValues(i) Then Exit Function
        End If
    Next i

    DoesCandidateMatchGroup = True
End Function

Private Sub ApplyCandidateLanceSequence(ByRef hasLance() As Boolean, ByRef lanceValues() As Long, ByVal groupStart As Long, ByVal groupEnd As Long, ByVal candidateSeq As String)
    Dim parts() As String
    Dim i As Long

    parts = Split(candidateSeq, ",")
    For i = groupStart To groupEnd
        If Not hasLance(i) Then
            lanceValues(i) = CLng(Trim$(parts(i - groupStart)))
            hasLance(i) = True
        End If
    Next i
End Sub

Private Function BuildMissingLanceMessage(ByVal pilarName As String, ByRef sourceRows() As Long, ByVal groupStart As Long, ByVal groupEnd As Long) As String
    Dim firstRow As Long
    Dim lastRow As Long

    firstRow = sourceRows(groupStart)
    lastRow = sourceRows(groupEnd)

    If firstRow = lastRow Then
        BuildMissingLanceMessage = _
            "Nao foi possivel identificar automaticamente o lance do pilar " & pilarName & "." & vbCrLf & _
            "Preencha o lance na linha " & firstRow & " e rode novamente."
    Else
        BuildMissingLanceMessage = _
            "Nao foi possivel identificar automaticamente os lances do pilar " & pilarName & "." & vbCrLf & _
            "Preencha os lances nas linhas " & firstRow & " a " & lastRow & " e rode novamente."
    End If
End Function

Private Function IsArmpilInputRowEmpty(ByVal pilarValue As Variant, ByVal lanceValue As Variant, ByVal qtyValue As Variant, ByVal diamValue As Variant) As Boolean
    IsArmpilInputRowEmpty = _
        Trim$(CStr(pilarValue)) = "" And _
        Trim$(CStr(lanceValue)) = "" And _
        Trim$(CStr(qtyValue)) = "" And _
        Trim$(CStr(diamValue)) = ""
End Function

Private Sub AppendArmpilValidationIssue(ByRef issueList As String, ByRef issueCount As Long, ByVal rowNumber As Long, ByVal detail As String)
    issueCount = issueCount + 1
    If issueCount <= 8 Then
        If issueList <> "" Then issueList = issueList & vbCrLf
        issueList = issueList & " - Linha " & rowNumber & ": " & detail
    ElseIf issueCount = 9 Then
        issueList = issueList & vbCrLf & " - ..."
    End If
End Sub

Private Function TryGetPositiveLong(ByVal cellValue As Variant, ByRef parsedValue As Long) As Boolean
    Dim parsedDouble As Double

    If Not TryGetPositiveDouble(cellValue, parsedDouble) Then Exit Function
    parsedValue = CLng(parsedDouble)
    If parsedDouble <> parsedValue Then Exit Function

    TryGetPositiveLong = (parsedValue > 0)
End Function

Private Function TryGetPositiveDouble(ByVal cellValue As Variant, ByRef parsedValue As Double) As Boolean
    Dim rawText As String

    rawText = CleanCSV(CStr(cellValue))
    If rawText = "" Then Exit Function

    parsedValue = Val(rawText)
    If parsedValue <= 0# Then Exit Function

    TryGetPositiveDouble = True
End Function

' ================================================================
' FORMATACAO / LIMPEZA
' ================================================================
Private Sub ClearARMPIL(ByVal ws As Worksheet)
    Dim lr As Long
    lr = GetLastUsedRowInColumns(ws, 2, 7)
    
    If lr >= 6 Then
        ws.Range(ws.Cells(6, 2), ws.Cells(lr, 7)).ClearContents
        ws.Range(ws.Cells(6, 2), ws.Cells(lr, 7)).Interior.Color = RGB(250, 251, 252)
        ws.Range(ws.Cells(6, 2), ws.Cells(lr, 7)).Font.Color = RGB(44, 62, 80)
        ws.Range(ws.Cells(6, 2), ws.Cells(lr, 7)).Font.Italic = False
    End If
End Sub

Private Sub ClearSELE(ByVal ws As Worksheet)
    Dim lr As Long
    lr = GetLastUsedRowInColumns(ws, 2, 5)
    
    If lr >= 6 Then
        ws.Range(ws.Cells(6, 2), ws.Cells(lr, 5)).ClearContents
        ws.Range(ws.Cells(6, 2), ws.Cells(lr, 5)).Interior.Color = RGB(250, 251, 252)
        ws.Range(ws.Cells(6, 2), ws.Cells(lr, 5)).Font.Color = RGB(44, 62, 80)
    End If
End Sub

Private Sub ClearAllTables()
    Dim oldCalc As XlCalculation
    Dim oldScreen As Boolean
    Dim oldEvents As Boolean
    Dim oldStatusBar As Variant

    oldCalc = Application.Calculation
    oldScreen = Application.ScreenUpdating
    oldEvents = Application.EnableEvents
    oldStatusBar = Application.StatusBar

    On Error GoTo Cleanup

    Application.ScreenUpdating = False
    Application.EnableEvents = False
    Application.Calculation = xlCalculationManual
    Application.StatusBar = "Limpando tabelas..."

    Dim wsArm As Worksheet
    Dim wsSel As Worksheet
    Dim wsRes As Worksheet

    Set wsArm = ThisWorkbook.Sheets("ARMPIL")
    Set wsSel = ThisWorkbook.Sheets("SELE")
    Set wsRes = ThisWorkbook.Sheets("RESULTADO")

    Dim lastRes As Long
    lastRes = wsRes.Cells(wsRes.Rows.count, 2).End(xlUp).Row
    If lastRes >= 9 Then
        wsRes.Range(wsRes.Cells(9, 2), wsRes.Cells(lastRes, 10)).FormatConditions.Delete
    End If

    ClearARMPIL wsArm
    ClearSELE wsSel
    ClearResultsPermanent wsRes

    SetArmpilManualHint wsArm
    wsArm.Cells(4, 2).Value = "  Nenhum ARMPIL carregado."
    wsSel.Cells(4, 2).Value = "  Nenhum SELE carregado."

Cleanup:
    Application.StatusBar = oldStatusBar
    Application.Calculation = oldCalc
    Application.ScreenUpdating = oldScreen
    Application.EnableEvents = oldEvents

    If Err.Number <> 0 Then
        Err.Raise Err.Number, , Err.Description
    End If
End Sub

Private Sub FormatInputRange(ByVal ws As Worksheet, ByVal rowStart As Long, ByVal rowEnd As Long, ByVal colStart As Long, ByVal colEnd As Long)
    If rowEnd < rowStart Then Exit Sub

    With ws.Range(ws.Cells(rowStart, colStart), ws.Cells(rowEnd, colEnd))
        .Borders.LineStyle = xlContinuous
        .Borders.Weight = xlThin
        .VerticalAlignment = xlCenter
    End With
End Sub

Private Function GetRequiredWorksheet(ByVal sheetName As String) As Worksheet
    On Error Resume Next
    Set GetRequiredWorksheet = ThisWorkbook.Worksheets(sheetName)
    On Error GoTo 0

    If GetRequiredWorksheet Is Nothing Then
        Err.Raise vbObjectError + 2100, , "A aba '" & sheetName & "' nao foi encontrada nesta pasta de trabalho."
    End If
End Function

Private Function BuildStageSuffix(ByVal stage As String) As String
    If Trim$(stage) <> "" Then BuildStageSuffix = " na etapa '" & stage & "'"
End Function

Private Function GetLastUsedRowInColumns(ByVal ws As Worksheet, ByVal colStart As Long, ByVal colEnd As Long) As Long
    Dim col As Long
    Dim candidate As Long

    For col = colStart To colEnd
        candidate = ws.Cells(ws.Rows.count, col).End(xlUp).Row
        If candidate > GetLastUsedRowInColumns Then GetLastUsedRowInColumns = candidate
    Next col
End Function

Private Function GetLastArmpilDataRow(ByVal ws As Worksheet) As Long
    GetLastArmpilDataRow = GetLastUsedRowInColumns(ws, 2, 5)
    If GetLastArmpilDataRow < 6 Then GetLastArmpilDataRow = 5
End Function

Private Function GetPilarBlockFillColor(ByVal blockIndex As Long) As Long
    If (blockIndex Mod 2) = 0 Then
        GetPilarBlockFillColor = RGB(235, 244, 255)
    Else
        GetPilarBlockFillColor = RGB(255, 249, 232)
    End If
End Function

Private Sub ApplyPilarBlockColors(ByVal ws As Worksheet, ByVal rowStart As Long, ByVal rowEnd As Long, ByVal pilarCol As Long, ByVal colStart As Long, ByVal colEnd As Long)
    Dim currentStart As Long
    Dim currentPilar As String
    Dim blockIndex As Long
    Dim i As Long
    Dim fillColor As Long

    If rowEnd < rowStart Then Exit Sub

    currentStart = rowStart
    currentPilar = NormalizePilarName(CStr(ws.Cells(rowStart, pilarCol).Value2))
    blockIndex = 0

    For i = rowStart + 1 To rowEnd + 1
        If i > rowEnd Or NormalizePilarName(CStr(ws.Cells(i, pilarCol).Value2)) <> currentPilar Then
            fillColor = GetPilarBlockFillColor(blockIndex)

            With ws.Range(ws.Cells(currentStart, colStart), ws.Cells(i - 1, colEnd)).Interior
                .Pattern = xlSolid
                .Color = fillColor
            End With
            currentStart = i
            blockIndex = blockIndex + 1
            If i <= rowEnd Then currentPilar = NormalizePilarName(CStr(ws.Cells(i, pilarCol).Value2))
        End If
    Next i
End Sub

Private Sub ApplyArmpilFormatting(ByVal ws As Worksheet, ByVal rowStart As Long, ByVal rowEnd As Long)
    If rowEnd < rowStart Then Exit Sub

    Dim rg As Range
    Set rg = ws.Range(ws.Cells(rowStart, 2), ws.Cells(rowEnd, 7))

    FormatInputRange ws, rowStart, rowEnd, 2, 7

    With rg
        .Font.Name = "Segoe UI"
        .Font.Size = 9
        .Font.Color = RGB(44, 62, 80)
        .HorizontalAlignment = xlCenter
        .VerticalAlignment = xlCenter
    End With

    ws.Range(ws.Cells(rowStart, 2), ws.Cells(rowEnd, 2)).Font.Bold = True
    ws.Rows(rowStart & ":" & rowEnd).RowHeight = 16

    ApplyPilarBlockColors ws, rowStart, rowEnd, 2, 2, 7
End Sub

Private Sub SetArmpilManualHint(ByVal ws As Worksheet)
    With ws.Cells(3, 2)
        .Value = "Edicao manual: preencha numero do Pilar, Qtd(Qf) e Bitola(mm). O lance pode ficar em branco se a sequencia puder ser inferida. Depois rode 'Atualizar ARMPIL Manual'."
        .Font.Name = "Segoe UI"
        .Font.Size = 9
        .Font.Color = RGB(90, 90, 90)
        .Font.Italic = True
    End With
End Sub

Private Function GetPilarSortNumber(ByVal pilar As String) As Double
    Dim txt As String
    Dim pos As Long
    Dim digits As String

    txt = NormalizePilarName(pilar)
    If Left$(txt, 3) = "PAF" Then
        pos = 4
    ElseIf Left$(txt, 1) = "P" Then
        pos = 2
    Else
        pos = 1
    End If

    Do While pos <= Len(txt) And Mid$(txt, pos, 1) Like "#"
        digits = digits & Mid$(txt, pos, 1)
        pos = pos + 1
    Loop

    If digits = "" Then
        GetPilarSortNumber = 1000000000#
    Else
        GetPilarSortNumber = CDbl(digits)
    End If
End Function

Private Function GetPilarPrefixRank(ByVal pilar As String) As Long
    Dim txt As String
    txt = NormalizePilarName(pilar)

    If Left$(txt, 1) = "P" And Left$(txt, 3) <> "PAF" Then
        GetPilarPrefixRank = 0
    ElseIf Left$(txt, 3) = "PAF" Then
        GetPilarPrefixRank = 1
    Else
        GetPilarPrefixRank = 9
    End If
End Function

Private Function GetPilarSuffix(ByVal pilar As String) As String
    Dim txt As String
    Dim pos As Long

    txt = NormalizePilarName(pilar)
    If Left$(txt, 3) = "PAF" Then
        pos = 4
    ElseIf Left$(txt, 1) = "P" Then
        pos = 2
    Else
        pos = 1
    End If

    Do While pos <= Len(txt) And Mid$(txt, pos, 1) Like "#"
        pos = pos + 1
    Loop

    GetPilarSuffix = Mid$(txt, pos)
End Function

Private Sub SortSheetRangeByPilarLance(ByVal ws As Worksheet, ByVal rowStart As Long, ByVal rowEnd As Long, ByVal firstCol As Long, ByVal lastCol As Long, ByVal pilarCol As Long, ByVal lanceCol As Long, ByVal helperStartCol As Long)
    If rowEnd < rowStart Then Exit Sub

    Dim rowCount As Long
    rowCount = rowEnd - rowStart + 1
    If rowCount <= 1 Then Exit Sub

    Dim src As Variant
    src = ws.Range(ws.Cells(rowStart, pilarCol), ws.Cells(rowEnd, pilarCol)).Value2

    Dim helperData() As Variant
    ReDim helperData(1 To rowCount, 1 To 3)

    Dim i As Long
    For i = 1 To rowCount
        helperData(i, 1) = GetPilarSortNumber(CStr(src(i, 1)))
        helperData(i, 2) = GetPilarPrefixRank(CStr(src(i, 1)))
        helperData(i, 3) = GetPilarSuffix(CStr(src(i, 1)))
    Next i

    ws.Range(ws.Cells(rowStart, helperStartCol), ws.Cells(rowEnd, helperStartCol + 2)).Value2 = helperData

    With ws.Sort
        .SortFields.Clear
        .SortFields.Add Key:=ws.Range(ws.Cells(rowStart, helperStartCol), ws.Cells(rowEnd, helperStartCol)), SortOn:=xlSortOnValues, Order:=xlAscending, DataOption:=xlSortNormal
        .SortFields.Add Key:=ws.Range(ws.Cells(rowStart, helperStartCol + 1), ws.Cells(rowEnd, helperStartCol + 1)), SortOn:=xlSortOnValues, Order:=xlAscending, DataOption:=xlSortNormal
        .SortFields.Add Key:=ws.Range(ws.Cells(rowStart, helperStartCol + 2), ws.Cells(rowEnd, helperStartCol + 2)), SortOn:=xlSortOnValues, Order:=xlAscending, DataOption:=xlSortNormal
        .SortFields.Add Key:=ws.Range(ws.Cells(rowStart, lanceCol), ws.Cells(rowEnd, lanceCol)), SortOn:=xlSortOnValues, Order:=xlAscending, DataOption:=xlSortNormal
        .SetRange ws.Range(ws.Cells(rowStart, firstCol), ws.Cells(rowEnd, helperStartCol + 2))
        .Header = xlNo
        .MatchCase = False
        .Orientation = xlTopToBottom
        .Apply
    End With

    ws.Range(ws.Cells(rowStart, helperStartCol), ws.Cells(rowEnd, helperStartCol + 2)).ClearContents
End Sub

Private Sub ApplySeleFormatting(ByVal ws As Worksheet, ByVal rowStart As Long, ByVal rowEnd As Long)
    If rowEnd < rowStart Then Exit Sub

    Dim rg As Range
    Set rg = ws.Range(ws.Cells(rowStart, 2), ws.Cells(rowEnd, 5))

    With rg
        .Font.Name = "Segoe UI"
        .Font.Size = 9
        .Font.Color = RGB(44, 62, 80)
        .HorizontalAlignment = xlCenter
        .VerticalAlignment = xlCenter
    End With

    ws.Range(ws.Cells(rowStart, 2), ws.Cells(rowEnd, 2)).Font.Bold = True
    ws.Rows(rowStart & ":" & rowEnd).RowHeight = 16

    ApplyPilarBlockColors ws, rowStart, rowEnd, 2, 2, 5
End Sub


Private Sub ClearResultsPermanent(ByVal ws As Worksheet)
    Dim lr As Long
    lr = ws.Cells(ws.Rows.count, 2).End(xlUp).Row

    PrepararCabecalhoResultado ws

    If lr >= 9 Then
        ws.Range(ws.Cells(9, 2), ws.Cells(lr, 10)).ClearContents
        ws.Range(ws.Cells(9, 2), ws.Cells(lr, 10)).Interior.Color = RGB(247, 248, 252)
        ws.Range(ws.Cells(9, 2), ws.Cells(lr, 10)).Font.Color = RGB(44, 62, 80)
    End If

    ws.Range(ws.Cells(6, 2), ws.Cells(6, 7)).Value = "--"
End Sub

Private Sub PrepararCabecalhoResultado(ByVal ws As Worksheet)
    With ws.Range("B1:J7")
        .UnMerge
        .ClearContents
        .Interior.Pattern = xlNone
        .Borders.LineStyle = xlNone
        .Font.Name = "Segoe UI"
        .Font.Color = RGB(30, 30, 28)
    End With

    With ws.Range("B1:J1")
        .Merge
        .Value = "AUDITORIA DE ARMADURA - ARMPIL x SELE"
        .Interior.Color = RGB(30, 30, 28)
        .Font.Color = RGB(255, 255, 255)
        .Font.Bold = True
        .Font.Size = 13
        .HorizontalAlignment = xlLeft
        .VerticalAlignment = xlCenter
    End With

    With ws.Range("B2:J2")
        .Merge
        .Value = "Compara As projetada no ARMPIL com As minima do SELE. Vermelho = nao atende o minimo."
        .Font.Italic = True
        .Font.Size = 9
        .Font.Color = RGB(90, 90, 90)
        .HorizontalAlignment = xlLeft
        .VerticalAlignment = xlCenter
    End With

    ws.Range("B5:G5").Value = Array("PILARES", "LANCES", "APROVADOS", "MARGEM 15%", "REPROVADOS", "SEM MATCH")

    With ws.Range("B5:G5")
        .Interior.Color = RGB(234, 243, 222)
        .Font.Bold = True
        .Font.Size = 9
        .HorizontalAlignment = xlCenter
        .VerticalAlignment = xlCenter
        .Borders.LineStyle = xlContinuous
        .Borders.Color = RGB(180, 178, 169)
    End With

    With ws.Range("B6:G6")
        .Interior.Color = RGB(248, 247, 244)
        .Font.Bold = True
        .Font.Size = 11
        .Font.Color = RGB(59, 109, 17)
        .HorizontalAlignment = xlCenter
        .VerticalAlignment = xlCenter
        .Borders.LineStyle = xlContinuous
        .Borders.Color = RGB(180, 178, 169)
    End With

    ws.Rows("1:7").RowHeight = 20
    ws.Rows(1).RowHeight = 28
End Sub

Private Sub FormatResultadoRange(ByVal ws As Worksheet, ByVal rowStart As Long, ByVal rowEnd As Long)
    If rowEnd < rowStart Then Exit Sub

    Dim rg As Range
    Set rg = ws.Range(ws.Cells(rowStart, 2), ws.Cells(rowEnd, 10))

    With rg
        .Font.Name = "Segoe UI"
        .Font.Size = 9
        .HorizontalAlignment = xlCenter
        .VerticalAlignment = xlCenter
        .Borders(xlEdgeBottom).LineStyle = xlContinuous
        .Borders(xlEdgeBottom).Color = RGB(189, 195, 208)
    End With

    ws.Range(ws.Cells(rowStart, 5), ws.Cells(rowEnd, 8)).NumberFormat = "0.00"
    ws.Range(ws.Cells(rowStart, 9), ws.Cells(rowEnd, 9)).NumberFormat = "+0.00;-0.00;0.00"
    ws.Range(ws.Cells(rowStart, 2), ws.Cells(rowEnd, 2)).Font.Bold = True
    ws.Range(ws.Cells(rowStart, 10), ws.Cells(rowEnd, 10)).Font.Bold = True
    ws.Rows(rowStart & ":" & rowEnd).RowHeight = 20
End Sub

Private Sub AtualizarResumoResultado(ByVal ws As Worksheet, ByVal lastRow As Long)
    If lastRow < 9 Then Exit Sub

    ws.Cells(6, 2).FormulaLocal = "=SOMARPRODUTO((B9:B" & lastRow & "<>"""")/CONT.SE(B9:B" & lastRow & ";B9:B" & lastRow & "&""""))"
    ws.Cells(6, 3).FormulaLocal = "=CONT.VALORES(B9:B" & lastRow & ")"
    ws.Cells(6, 4).FormulaLocal = "=CONT.SE(J9:J" & lastRow & ";""APROVADO"")"
    ws.Cells(6, 5).FormulaLocal = "=CONT.SE(J9:J" & lastRow & ";""MARGEM 15%"")"
    ws.Cells(6, 6).FormulaLocal = "=CONT.SE(J9:J" & lastRow & ";""REPROVADO"")"
    ws.Cells(6, 7).FormulaLocal = "=CONT.SE(J9:J" & lastRow & ";""SEM MATCH"")"
    ws.Range(ws.Cells(6, 2), ws.Cells(6, 7)).Calculate
End Sub

Private Sub ConfigurarFormatacaoCondicionalResultado(ByVal ws As Worksheet, ByVal lastRow As Long)
    If lastRow < 9 Then Exit Sub

    Dim rg As Range
    Set rg = ws.Range(ws.Cells(9, 2), ws.Cells(lastRow, 10))

    rg.FormatConditions.Delete

    ' APROVADO
    With rg.FormatConditions.Add(Type:=xlExpression, Formula1:="=$J9=""APROVADO""")
        .Interior.Color = RGB(213, 245, 227)
        .Font.Color = RGB(30, 132, 73)
    End With

    ' MARGEM 15%
    With rg.FormatConditions.Add(Type:=xlExpression, Formula1:="=$J9=""MARGEM 15%""")
        .Interior.Color = RGB(255, 249, 196)
        .Font.Color = RGB(133, 100, 4)
    End With

    ' REPROVADO
    With rg.FormatConditions.Add(Type:=xlExpression, Formula1:="=$J9=""REPROVADO""")
        .Interior.Color = RGB(255, 204, 204)
        .Font.Color = RGB(192, 57, 43)
    End With

    ' SEM MATCH
    With rg.FormatConditions.Add(Type:=xlExpression, Formula1:="=$J9=""SEM MATCH""")
        .Interior.Color = RGB(255, 249, 196)
        .Font.Color = RGB(133, 100, 4)
    End With
End Sub
