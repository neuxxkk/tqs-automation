VERSION 5.00
Begin {C62A69F0-16DC-11CE-9E98-00AA00574A4F} frmArmpilLanceMap 
   Caption         =   "UserForm1"
   ClientHeight    =   3015
   ClientLeft      =   120
   ClientTop       =   465
   ClientWidth     =   4560
   OleObjectBlob   =   "frmArmpilLanceMap.frx":0000
   StartUpPosition =   1  'CenterOwner
End
Attribute VB_Name = "frmArmpilLanceMap"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = True
Attribute VB_Exposed = False
Option Explicit

Private Const FORM_WIDTH As Single = 780
Private Const FORM_HEIGHT As Single = 560
Private Const ROW_HEIGHT As Single = 22
Private Const HEADER_HEIGHT As Single = 22
Private Const FRAME_SCROLL_VERTICAL As Long = 2
Private Const FRAME_KEEP_SCROLLBAR_VISIBLE As Long = 2
Private Const TEXT_ALIGN_LEFT As Long = 1
Private Const TEXT_ALIGN_CENTER As Long = 2
Private Const BACKSTYLE_OPAQUE As Long = 1

Private mAllLevelsCsv As String
Private mIdentifiedLevelsCsv As String
Private mDefaultPairs As String
Private mResultMapText As String

Public Sub SetupEditor( _
    ByVal allLevelsCsv As String, _
    ByVal identifiedLevelsCsv As String, _
    ByVal defaultMap As String, _
    ByVal defaultPairs As String _
)
    mAllLevelsCsv = Trim$(allLevelsCsv)
    mIdentifiedLevelsCsv = Trim$(identifiedLevelsCsv)
    mDefaultPairs = Trim$(defaultPairs)
    mResultMapText = ""

    Me.Width = FORM_WIDTH
    Me.Height = FORM_HEIGHT
    Me.backColor = RGB(245, 247, 250)
    lblError.Visible = False
    fraLevels.ScrollTop = 0
    PopulateRows defaultMap
End Sub

Public Property Get ResultMapText() As String
    ResultMapText = mResultMapText
End Property

Private Sub cmdConfirm_Click()
    Dim quickText As String
    Dim startText As String
    Dim desiredStart As Long
    Dim rawLances As String
    Dim mapText As String

    quickText = Trim$(CStr(txtQuick.text))
    If quickText <> "" Then
        mapText = BuildLanceMapFromLists(mAllLevelsCsv, quickText)
    Else
        rawLances = BuildRawLancesCsv()
        If rawLances = "" Then
            ShowValidationMessage BuildArmpilMapErrorMessage(mDefaultPairs)
            Exit Sub
        End If

        startText = Trim$(CStr(txtStart.text))
        If startText <> "" Then
            If Not IsNumeric(startText) Then
                ShowValidationMessage "O campo 'Primeiro lance' deve ser numerico."
                Exit Sub
            End If

            desiredStart = CLng(Val(startText))
            If desiredStart <= 0 Then
                ShowValidationMessage "O campo 'Primeiro lance' deve ser maior que zero."
                Exit Sub
            End If

            rawLances = ShiftLanceCsvStart(rawLances, desiredStart)
            If rawLances = "" Then
                ShowValidationMessage BuildArmpilMapErrorMessage(mDefaultPairs)
                Exit Sub
            End If
        End If

        mapText = BuildLanceMapFromLists(mAllLevelsCsv, rawLances)
    End If

    If mapText = "" Then
        ShowValidationMessage BuildArmpilMapErrorMessage(mDefaultPairs)
        Exit Sub
    End If

    mResultMapText = mapText
    Me.Hide
End Sub

Private Sub cmdCancel_Click()
    mResultMapText = ""
    Me.Hide
End Sub

Private Sub UserForm_QueryClose(Cancel As Integer, CloseMode As Integer)
    If CloseMode = 0 Then
        Cancel = True
        cmdCancel_Click
    End If
End Sub

Private Sub UserForm_Activate()
    On Error Resume Next
    txtQuick.SetFocus
    On Error GoTo 0
End Sub

Private Sub PopulateRows(ByVal defaultMap As String)
    Dim levelParts() As String
    Dim defaultEntriesCsv As String
    Dim defaultLances() As String
    Dim levelCount As Long
    Dim i As Long
    Dim topPos As Single
    Dim normalizedLevel As String
    Dim isUsefulLevel As Boolean
    Dim defaultLanceText As String
    Dim statusText As String
    Dim rowBackColor As Long
    Dim statusBackColor As Long
    Dim firstPositiveLance As Long

    ClearFrameControls
    AddFrameHeader

    levelParts = Split(mAllLevelsCsv, ",")
    levelCount = UBound(levelParts) - LBound(levelParts) + 1
    defaultEntriesCsv = BuildLanceEntriesForLevels(mAllLevelsCsv, defaultMap)
    defaultLances = Split(defaultEntriesCsv, ",")
    firstPositiveLance = GetFirstPositiveLanceFromCsv(defaultEntriesCsv)

    If firstPositiveLance > 0 Then
        txtStart.text = CStr(firstPositiveLance)
    Else
        txtStart.text = ""
    End If

    topPos = 34
    For i = 0 To levelCount - 1
        normalizedLevel = NormalizeLevelToken(levelParts(i))
        isUsefulLevel = CsvContainsNormalizedLevel(mIdentifiedLevelsCsv, normalizedLevel)
        defaultLanceText = ""
        If defaultEntriesCsv <> "" Then
            If i <= UBound(defaultLances) Then defaultLanceText = Trim$(defaultLances(i))
        End If

        If isUsefulLevel Then
            statusText = "Com armadura"
            rowBackColor = RGB(255, 255, 255)
            statusBackColor = RGB(236, 253, 245)
        Else
            statusText = "Detectado no PDF"
            rowBackColor = RGB(248, 250, 252)
            statusBackColor = RGB(241, 245, 249)
        End If

        AddFrameLabel "lvl_" & CStr(i), 6, topPos, 96, ROW_HEIGHT, "+" & normalizedLevel, False, rowBackColor, RGB(55, 65, 81), TEXT_ALIGN_CENTER
        With AddFrameLabel("ctx_" & CStr(i), 104, topPos, 356, ROW_HEIGHT, BuildLevelContext(levelParts, i), False, rowBackColor, RGB(55, 65, 81), TEXT_ALIGN_LEFT)
            .WordWrap = True
        End With
        With AddFrameTextBox("txtLance_" & CStr(i), 462, topPos, 76, ROW_HEIGHT, defaultLanceText)
            .textAlign = TEXT_ALIGN_CENTER
            .backColor = RGB(255, 248, 220)
        End With
        AddFrameLabel "sts_" & CStr(i), 540, topPos, 170, ROW_HEIGHT, statusText, False, statusBackColor, IIf(isUsefulLevel, RGB(22, 101, 52), RGB(71, 85, 105)), TEXT_ALIGN_CENTER

        topPos = topPos + ROW_HEIGHT + 4
    Next i

    fraLevels.ScrollBars = FRAME_SCROLL_VERTICAL
    fraLevels.KeepScrollBarsVisible = FRAME_KEEP_SCROLLBAR_VISIBLE
    fraLevels.ScrollHeight = topPos + 8
    fraLevels.ScrollTop = 0
    lblError.Visible = False
End Sub

Private Function BuildRawLancesCsv() As String
    Dim levelCount As Long
    Dim i As Long
    Dim text As String
    Dim lanceValue As Long
    Dim txt As Object

    levelCount = CountCsvItems(mAllLevelsCsv)
    If levelCount <= 0 Then Exit Function

    For i = 0 To levelCount - 1
        If i > 0 Then BuildRawLancesCsv = BuildRawLancesCsv & ","

        Set txt = fraLevels.Controls("txtLance_" & CStr(i))
        text = Trim$(CStr(txt.text))
        If text = "" Then
            BuildRawLancesCsv = BuildRawLancesCsv & "0"
            GoTo NextItem
        End If

        If Not IsNumeric(text) Then Exit Function
        lanceValue = CLng(Val(text))
        If lanceValue < 0 Then Exit Function

        BuildRawLancesCsv = BuildRawLancesCsv & CStr(lanceValue)
NextItem:
    Next i
End Function

Private Sub ShowValidationMessage(ByVal messageText As String)
    lblError.Caption = "Entrada invalida. Revise os campos e tente novamente."
    lblError.Visible = True
    MsgBox messageText, vbExclamation, "Mapear lances ARMPIL"
End Sub

Private Sub ClearFrameControls()
    Dim i As Long

    For i = fraLevels.Controls.Count - 1 To 0 Step -1
        fraLevels.Controls.Remove fraLevels.Controls(i).Name
    Next i
End Sub

Private Sub AddFrameHeader()
    AddFrameLabel "hdrLevel", 6, 6, 96, HEADER_HEIGHT, "Nivel", True, RGB(95, 122, 138), RGB(255, 255, 255), TEXT_ALIGN_CENTER
    AddFrameLabel "hdrContext", 104, 6, 356, HEADER_HEIGHT, "Trecho atendido", True, RGB(95, 122, 138), RGB(255, 255, 255), TEXT_ALIGN_CENTER
    AddFrameLabel "hdrLance", 462, 6, 76, HEADER_HEIGHT, "Lance", True, RGB(95, 122, 138), RGB(255, 255, 255), TEXT_ALIGN_CENTER
    AddFrameLabel "hdrStatus", 540, 6, 170, HEADER_HEIGHT, "Status", True, RGB(95, 122, 138), RGB(255, 255, 255), TEXT_ALIGN_CENTER
End Sub

Private Function AddFrameLabel( _
    ByVal controlName As String, _
    ByVal leftPos As Single, _
    ByVal topPos As Single, _
    ByVal widthPos As Single, _
    ByVal heightPos As Single, _
    ByVal captionText As String, _
    ByVal isBold As Boolean, _
    ByVal backColor As Long, _
    ByVal foreColor As Long, _
    ByVal textAlign As Long _
) As Object
    Dim lbl As Object

    Set lbl = fraLevels.Controls.Add("Forms.Label.1", controlName, True)
    With lbl
        .Left = leftPos
        .Top = topPos
        .Width = widthPos
        .Height = heightPos
        .Caption = captionText
        .Font.Name = "Segoe UI"
        .Font.Size = 9
        .Font.Bold = isBold
        .foreColor = foreColor
        .BackStyle = BACKSTYLE_OPAQUE
        .backColor = backColor
        .BorderStyle = fmBorderStyleSingle
        .textAlign = textAlign
    End With

    Set AddFrameLabel = lbl
End Function

Private Function AddFrameTextBox( _
    ByVal controlName As String, _
    ByVal leftPos As Single, _
    ByVal topPos As Single, _
    ByVal widthPos As Single, _
    ByVal heightPos As Single, _
    ByVal defaultText As String _
) As Object
    Dim txt As Object

    Set txt = fraLevels.Controls.Add("Forms.TextBox.1", controlName, True)
    With txt
        .Left = leftPos
        .Top = topPos
        .Width = widthPos
        .Height = heightPos
        .text = defaultText
        .Font.Name = "Segoe UI"
        .Font.Size = 9
        .BorderStyle = fmBorderStyleSingle
        .backColor = RGB(255, 250, 205)
    End With

    Set AddFrameTextBox = txt
End Function

