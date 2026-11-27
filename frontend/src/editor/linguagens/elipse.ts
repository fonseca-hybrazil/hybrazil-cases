// VBScript do Elipse E3: o VBScript padrão do highlight.js + objetos, funções globais (E3Globals)
// e membros (métodos/propriedades) documentados no Manual de Scripts do E3 (docs.elipse.com.br).
import type { HLJSApi, Language } from 'highlight.js'
import vbscript from 'highlight.js/lib/languages/vbscript'

// Objetos acessíveis diretamente nos scripts
const OBJETOS = ['Application', 'Screen', 'Parent', 'Frame']

// Funções globais do E3 (E3Globals)
const GLOBAIS = [
  'BShl', 'BShr', 'Choose', 'E3Format', 'GetBit', 'SetBit', 'GetComputerName', 'GetCurrentWindowsUserName',
  'GetLocalTime', 'GetLocalTimeUTC', 'IIf', 'MsgBoxEx', 'OPCGetQuality', 'OPCIsGood', 'OPCIsBad', 'OPCIsUncertain',
  'OPCMakeQuality', 'OPCSetQuality', 'SourceTypeName', 'XQuery',
]

// Constantes do E3
const CONSTANTES = ['etOnEvent', 'etWhileEvent']

// Métodos e propriedades usados depois do ponto (ex.: Application.GetObject, tag.Quality)
const MEMBROS = [
  // comuns a todos os objetos
  'Activate', 'AddObject', 'Context', 'Deactivate', 'DeleteObject', 'GetChildObject', 'GetObject', 'Item',
  'RunEvent', 'RunProcedure', 'Save', 'CreateLink', 'RemoveLink', 'AddUserEvent', 'RemoveUserEvent', 'AddScript',
  'RemoveAll', 'Application', 'Count', 'DocString', 'ExposeToOpc', 'IsObjectActive', 'Links', 'Name',
  'ObjectEvents', 'Parent', 'PathContainer', 'PathName', 'PathVolume', 'Property', 'Source', 'Type',
  // Viewer
  'CaptureScreen', 'ChangePassword', 'ChangeUserPassword', 'DoModal', 'ESign', 'ExecuteExternalApp', 'Exit',
  'GetFormulaUnitDataObj', 'GetFormulaValueDataObj', 'GetFrame', 'GetFullUserName', 'GetKeyPad', 'GetMouseX',
  'GetMouseY', 'GetScreen', 'GetValue', 'IsAppRunning', 'IsUserMemberOfGroup', 'IsWebViewer', 'LoadFormulaDlg',
  'LoadFormulaValues', 'LoadReport', 'Login', 'LoginUser', 'LoginWindowsUser', 'Logout', 'PasswordConfirm',
  'Playsound', 'SelectMenu', 'SetValue', 'ShowDatePicker', 'ShowFilePicker', 'ShowPickColor', 'ShowTrendAnalysis',
  'Stopsound', 'ToggleValue', 'Trace', 'TrackEvent', 'UserAdministration', 'User',
  // Servidor
  'ReportFailure', 'AckFailure', 'ClearFailure', 'E3GetActor',
  // Quadros (Frame/Splitter) e telas
  'OpenScreen', 'Close', 'BringToFront', 'MaximizeFrame', 'MinimizeFrame', 'MoveFrame', 'RestoreFrame',
  'FlashWindow', 'NavigateBack', 'NavigateForward', 'Refresh', 'SetFrameOptions', 'ShowScreen',
  'FromPixelX', 'FromPixelY', 'ToPixelX', 'ToPixelY',
  // objetos de tela
  'Visible', 'Enabled', 'BackgroundColor', 'ForegroundColor', 'X', 'Y', 'Width', 'Height', 'Tip', 'SetFocus',
  'SendToBack',
  // tags
  'Value', 'Quality', 'TimeStamp', 'RawValue', 'Write', 'WriteEx', 'AllowRead', 'AllowWrite', 'Scan', 'EU',
  'EULow', 'EUHigh', 'EnableScaling', 'ParamDevice', 'ParamItem', 'Retentive', 'Reset', 'Preset',
  // consultas, alarmes e históricos
  'Execute', 'GetADORecordset', 'SetVariableValue', 'SQL', 'Where', 'OrderBy',
  'AckAllAlarms', 'AckArea', 'LogTrackingEvent', 'ActiveAlarms', 'Ack', 'Shelve', 'Unshelve',
  'StartAcquisition', 'StopAcquisition', 'WriteRecord',
]

export default function elipse(hljs: HLJSApi): Language {
  const base = vbscript(hljs)
  const kw = base.keywords as Record<string, string[]>
  const membro = new RegExp(`(?:${[...MEMBROS].sort((a, b) => b.length - a.length).join('|')})\\b`)
  return {
    ...base,
    name: 'VBScript (Elipse E3)',
    aliases: ['e3', 'e3script'],
    disableAutodetect: true,   // na detecção automática, fica o VBScript comum
    keywords: {
      ...kw,
      built_in: [...kw.built_in, ...OBJETOS, ...GLOBAIS],
      literal: [...kw.literal, ...CONSTANTES],
    },
    contains: [
      // Sub CommandButton1_Click() / Function Calcula(x): nome do procedimento em destaque
      {
        match: [/\b(?:Sub|Function)\b/, /\s+/, /[A-Za-z_]\w*/],
        scope: { 1: 'keyword', 3: 'title.function' },
      },
      // .GetObject, .Value, .WriteEx ... (membros documentados do E3)
      { match: [/\./, membro], scope: { 2: 'property' }, relevance: 0 },
      ...(base.contains ?? []),
    ],
  }
}
