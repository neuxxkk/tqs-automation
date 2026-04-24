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

    ' Array somente para colunas B:E
    ' B = Pilar
    ' C = Lance
    ' D = Qtd(Qf)
    ' E = Bitola(mm)
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
            pilar = CleanCSV(parts(0))

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

    ' Fórmulas em bloco
    ' F = As Total = Qtd * PI * Bitola^2 / 4 / 100
    ws.Range("F6:F" & 5 + outRow).FormulaR1C1 = "=RC[-2]*PI()*(RC[-1]^2)/4/100"
    ws.Range("G6:G" & 5 + outRow).FormulaR1C1 = "=RC[-5]&""|""&RC[-4]"

    ' Formatação em bloco
    ws.Range("C6:C" & 5 + outRow).NumberFormat = "0"
    ws.Range("D6:E" & 5 + outRow).NumberFormat = "0.00"
    ws.Range("F6:F" & 5 + outRow).NumberFormat = "0.00"

    ' Se quiser manter alguma aparência/padrão
    FormatInputRange ws, 6, 5 + outRow, 2, 7

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

    ' --- 1. Lê o arquivo inteiro em memória (uma só vez) ---
    Dim lines As Variant
    lines = ReadAllNonEmptyLines(path)
    If Not IsArray(lines) Then GoTo Cleanup
    If UBound(lines) < LBound(lines) Then GoTo Cleanup

    ' --- 2. 1ª passagem: descobre lances disponíveis ---
    Dim lancesDict As Object
    Set lancesDict = CreateObject("Scripting.Dictionary")

    Dim currentPilar As String: currentPilar = ""
    Dim i As Long, lanceNum As Long, asVal As Double

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
P1Next:
    Next i

    If lancesDict.count = 0 Then GoTo Cleanup

    ' --- 3. Ordena os lances e monta string para o diálogo ---
    Dim keys As Variant: keys = lancesDict.keys
    Dim j As Long, tmp As Variant
    For i = 0 To UBound(keys) - 1
        For j = i + 1 To UBound(keys)
            If CLng(keys(i)) > CLng(keys(j)) Then
                tmp = keys(i): keys(i) = keys(j): keys(j) = tmp
            End If
        Next j
    Next i

    Dim lanceList As String
    For i = 0 To UBound(keys)
        lanceList = lanceList & keys(i) & ", "
    Next i
    lanceList = Left$(lanceList, Len(lanceList) - 2)

    ' --- 4. Diálogo de seleção de níveis ---
    Dim dlgMsg As String
    dlgMsg = "Níveis encontrados no arquivo:" & vbCrLf & _
             "  " & lanceList & vbCrLf & vbCrLf & _
             "Informe os níveis a importar (separados por vírgula)." & vbCrLf & _
             "Deixe em branco para importar todos:"

    Dim resp As Variant
    resp = Application.InputBox(dlgMsg, "Selecionar Níveis", lanceList, Type:=2)
    If resp = False Then GoTo Cleanup   ' usuário clicou Cancelar

    ' Monta conjunto de filtro (Dictionary para lookup O(1))
    Dim filterSet As Object
    Set filterSet = CreateObject("Scripting.Dictionary")
    Dim filterActive As Boolean: filterActive = False

    Dim respStr As String: respStr = Trim$(CStr(resp))
    If respStr <> "" Then
        Dim parts() As String: parts = Split(respStr, ",")
        Dim p As Long
        For p = 0 To UBound(parts)
            Dim lvStr As String: lvStr = Trim$(parts(p))
            If IsNumeric(lvStr) Then filterSet(CLng(lvStr)) = True
        Next p
        filterActive = (filterSet.count > 0) And (filterSet.count < lancesDict.count)
    End If

    ' --- 5. 2ª passagem: coleta dados filtrados em arrays ---
    Dim maxRows As Long: maxRows = UBound(lines) - LBound(lines) + 1

    Dim arrPilar() As String:  ReDim arrPilar(1 To maxRows)
    Dim arrLance() As Long:    ReDim arrLance(1 To maxRows)
    Dim arrAs()    As Double:  ReDim arrAs(1 To maxRows)
    Dim arrAlt()   As Boolean: ReDim arrAlt(1 To maxRows)

    Dim rowCount As Long:  rowCount = 0
    Dim prevPilar As String: prevPilar = ""
    Dim altRow As Boolean:   altRow = False
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

        If currentPilar <> prevPilar Then
            altRow = Not altRow
            prevPilar = currentPilar
        End If

        rowCount = rowCount + 1
        arrPilar(rowCount) = currentPilar
        arrLance(rowCount) = lanceNum
        arrAs(rowCount) = asVal / 10#
        arrAlt(rowCount) = altRow
P2Next:
    Next i

    ' --- 6. Limpa e escreve ---
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
        colE(i, 1) = arrPilar(i) & "|" & CStr(arrLance(i))   ' valor direto, sem fórmula
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

    ApplySeleFormatting ws, startRow, endRow, arrAlt, rowCount

    ws.Cells(4, 2).value = "  Carregado: " & rowCount & " registros  |  " & path

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
Private Sub CompareAndMark()
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
    Set wsArm = ThisWorkbook.Sheets("ARMPIL")
    Set wsSel = ThisWorkbook.Sheets("SELE")
    Set wsRes = ThisWorkbook.Sheets("RESULTADO")

    ClearResultsPermanent wsRes

    Dim lastArm As Long, lastSel As Long
    lastArm = wsArm.Cells(wsArm.Rows.count, 2).End(xlUp).Row
    lastSel = wsSel.Cells(wsSel.Rows.count, 2).End(xlUp).Row

    If lastArm < 6 And lastSel < 6 Then
        MsgBox "Nenhum dado carregado em ARMPIL ou SELE.", vbExclamation
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
        .Range(.Cells(firstResRow, 4), .Cells(lastResRow, 4)).FormulaR1C1 = "=RC[-2]&""|""&RC[-1]"

        If lastArm >= 6 Then
            .Range(.Cells(firstResRow, 5), .Cells(lastResRow, 5)).FormulaR1C1 = _
                "=IFERROR(XLOOKUP(RC4,'ARMPIL'!R6C7:R" & lastArm & "C7,'ARMPIL'!R6C4:R" & lastArm & "C4),"""")"
            .Range(.Cells(firstResRow, 6), .Cells(lastResRow, 6)).FormulaR1C1 = _
                "=IFERROR(XLOOKUP(RC4,'ARMPIL'!R6C7:R" & lastArm & "C7,'ARMPIL'!R6C5:R" & lastArm & "C5),"""")"
            .Range(.Cells(firstResRow, 7), .Cells(lastResRow, 7)).FormulaR1C1 = _
                "=IFERROR(XLOOKUP(RC4,'ARMPIL'!R6C7:R" & lastArm & "C7,'ARMPIL'!R6C6:R" & lastArm & "C6),"""")"
        End If

        If lastSel >= 6 Then
            .Range(.Cells(firstResRow, 8), .Cells(lastResRow, 8)).FormulaR1C1 = _
                "=IFERROR(XLOOKUP(RC4,'SELE'!R6C5:R" & lastSel & "C5,'SELE'!R6C4:R" & lastSel & "C4),"""")"
        End If

        .Range(.Cells(firstResRow, 9), .Cells(lastResRow, 9)).FormulaR1C1 = _
            "=IF(OR(RC[-2]="""",RC[-1]=""""),"""",RC[-2]-RC[-1])"
        .Range(.Cells(firstResRow, 10), .Cells(lastResRow, 10)).FormulaR1C1 = _
            "=IF(OR(RC[-3]="""",RC[-2]=""""),""SEM MATCH"",IF(RC[-3]>=RC[-2],""APROVADO"",IF(RC[-3]*1.15>=RC[-2],""MARGEM 15%"",""REPROVADO"")))"
    End With

    FormatResultadoRange wsRes, firstResRow, lastResRow
    AtualizarResumoResultado wsRes, lastResRow
    ConfigurarFormatacaoCondicionalResultado wsRes, lastResRow

    wsRes.Activate
    MsgBox "Resultado preparado com fórmulas permanentes.", vbInformation

Cleanup:
    Application.EnableEvents = oldEvents
    Application.Calculation = oldCalc
    Application.ScreenUpdating = oldScreen
    If Err.Number <> 0 Then
        MsgBox "Erro na comparacao: " & Err.Description, vbExclamation
    End If
End Sub

Private Function RunPythonArmpilExtractor() As String
    Dim oldStatusBar As Variant
    Dim errNum As Long
    Dim errDesc As String

    oldStatusBar = Application.StatusBar
    Application.StatusBar = "Executando extrator ARMPIL..."

    On Error GoTo Cleanup

    Dim scriptPath As String
    scriptPath = GetArmpilScriptPath()
    If scriptPath = "" Then GoTo Cleanup

    Dim pythonExe As String
    Dim pythonArgs As String
    If Not GetPythonCommand(pythonExe, pythonArgs) Then
        Err.Raise vbObjectError + 2000, , "Python não encontrado. Instale o Python ou ajuste o launcher no VBA."
    End If

    Dim shellObj As Object
    Dim exitCode As Long
    Dim resultFile As String
    Dim launcherFile As String
    Dim resultText As String

    resultFile = Environ$("TEMP") & Application.PathSeparator & "armpil_result_" & Format$(Now, "yyyymmdd_hhnnss") & ".txt"
    launcherFile = Environ$("TEMP") & Application.PathSeparator & "armpil_run_" & Format$(Now, "yyyymmdd_hhnnss") & ".cmd"

    WriteTextFile launcherFile, BuildPythonLauncherScript(pythonExe, pythonArgs, scriptPath, resultFile)

    Set shellObj = CreateObject("WScript.Shell")
    exitCode = shellObj.Run("cmd.exe /d /c " & QuotePath(launcherFile), 0, True)

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

    If Dir$(RunPythonArmpilExtractor) = "" Then
        Err.Raise vbObjectError + 2003, , "CSV gerado não encontrado:" & vbCrLf & RunPythonArmpilExtractor
    End If

Cleanup:
    errNum = Err.Number
    errDesc = Err.Description
    Application.StatusBar = oldStatusBar
    If errNum <> 0 Then
        Err.Raise errNum, , errDesc
    End If
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

Private Function BuildPythonLauncherScript(ByVal exeName As String, ByVal exeArgs As String, ByVal scriptPath As String, ByVal resultFile As String) As String
    Dim lines As String

    lines = "@echo off" & vbCrLf
    lines = lines & "setlocal" & vbCrLf
    lines = lines & "set ""ARMPIL_RESULT_FILE=" & resultFile & """" & vbCrLf
    lines = lines & BuildExecutableCommand(exeName, exeArgs) & " " & QuotePath(scriptPath) & vbCrLf
    lines = lines & "exit /b %errorlevel%" & vbCrLf

    BuildPythonLauncherScript = lines
End Function

Private Function BuildPythonCheckScript(ByVal exeName As String, ByVal exeArgs As String) As String
    Dim lines As String

    lines = "@echo off" & vbCrLf
    lines = BuildExecutableCommand(exeName, exeArgs) & " -c ""import fitz""" & vbCrLf
    lines = "exit /b %errorlevel%" & vbCrLf

    BuildPythonCheckScript = lines
End Function

Private Function ExtractTaggedValue(ByVal text As String, ByVal tag As String) As String
    Dim pos As Long
    Dim endPos As Long

    pos = InStr(1, text, tag, vbTextCompare)
    If pos = 0 Then Exit Function

    pos = pos + Len(tag)
    endPos = InStr(pos, text, vbLf)
    If endPos = 0 Then endPos = Len(text) + 1

    ExtractTaggedValue = Trim$(Replace(Mid$(text, pos, endPos - pos), vbCr, ""))
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

    ExtractSelePilarName = Trim$(raw)
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
        pilar = Trim$(CStr(data(i, 1)))
        lanceTxt = Trim$(CStr(data(i, 2)))
        If pilar <> "" And lanceTxt <> "" Then
            chave = UCase$(pilar) & "|" & lanceTxt
            If Not dict.Exists(chave) Then dict.Add chave, Array(pilar, data(i, 2))
        End If
    Next i
End Sub

' ================================================================
' FORMATACAO / LIMPEZA
' ================================================================
Private Sub ClearARMPIL(ByVal ws As Worksheet)
    Dim lr As Long
    lr = ws.Cells(ws.Rows.count, 2).End(xlUp).Row
    
    If lr >= 6 Then
        ws.Range(ws.Cells(6, 2), ws.Cells(lr, 7)).ClearContents
        ws.Range(ws.Cells(6, 2), ws.Cells(lr, 7)).Interior.Color = RGB(250, 251, 252)
        ws.Range(ws.Cells(6, 2), ws.Cells(lr, 7)).Font.Color = RGB(44, 62, 80)
        ws.Range(ws.Cells(6, 2), ws.Cells(lr, 7)).Font.Italic = False
    End If
End Sub

Private Sub ClearSELE(ByVal ws As Worksheet)
    Dim lr As Long
    lr = ws.Cells(ws.Rows.count, 2).End(xlUp).Row
    
    If lr >= 6 Then
        ws.Range(ws.Cells(6, 2), ws.Cells(lr, 5)).ClearContents
        ws.Range(ws.Cells(6, 2), ws.Cells(lr, 5)).Interior.Color = RGB(250, 251, 252)
        ws.Range(ws.Cells(6, 2), ws.Cells(lr, 5)).Font.Color = RGB(44, 62, 80)
    End If
End Sub

Private Sub FormatInputRange(ByVal ws As Worksheet, ByVal rowStart As Long, ByVal rowEnd As Long, ByVal colStart As Long, ByVal colEnd As Long)
    With ws.Range(ws.Cells(rowStart, colStart), ws.Cells(rowEnd, colEnd))
        .Borders.LineStyle = xlContinuous
        .Borders.Weight = xlThin
        .VerticalAlignment = xlCenter
    End With
End Sub

Private Sub ApplySeleFormatting(ByVal ws As Worksheet, ByVal rowStart As Long, ByVal rowEnd As Long, ByRef arrAlt() As Boolean, ByVal rowCount As Long)
    If rowCount <= 0 Then Exit Sub

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

    Dim blockStart As Long
    Dim i As Long
    Dim fillColor As Long

    blockStart = 1
    For i = 2 To rowCount + 1
        If i > rowCount Or arrAlt(i) <> arrAlt(blockStart) Then
            If arrAlt(blockStart) Then
                fillColor = RGB(250, 251, 252)
            Else
                fillColor = RGB(255, 255, 255)
            End If

            ws.Range(ws.Cells(rowStart + blockStart - 1, 2), ws.Cells(rowStart + i - 2, 5)).Interior.Color = fillColor
            blockStart = i
        End If
    Next i
End Sub


Private Sub ClearResultsPermanent(ByVal ws As Worksheet)
    Dim lr As Long
    lr = ws.Cells(ws.Rows.count, 2).End(xlUp).Row

    If lr >= 9 Then
        ws.Range(ws.Cells(9, 2), ws.Cells(lr, 10)).ClearContents
        ws.Range(ws.Cells(9, 2), ws.Cells(lr, 10)).Interior.Color = RGB(247, 248, 252)
        ws.Range(ws.Cells(9, 2), ws.Cells(lr, 10)).Font.Color = RGB(44, 62, 80)
    End If

    ws.Cells(6, 2).value = "--"
    ws.Cells(6, 3).value = "--"
    ws.Cells(6, 4).value = "--"
    ws.Cells(6, 5).value = "--"
    ws.Cells(6, 6).value = "--"
    ws.Cells(6, 7).value = "--"
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
    ws.Cells(6, 5).FormulaLocal = "=CONT.SE(J9:J" & lastRow & ";""REPROVADO"")"
    ws.Cells(6, 6).FormulaLocal = "=CONT.SE(J9:J" & lastRow & ";""SEM MATCH"")"
    ws.Cells(6, 7).FormulaLocal = "=CONT.SE(J9:J" & lastRow & ";""MARGEM 15%"")"
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

