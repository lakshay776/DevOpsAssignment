{{- define "campusdesk.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "campusdesk.fullname" -}}
{{- if .Values.fullnameOverride -}}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- $name := default .Chart.Name .Values.nameOverride -}}
{{- if contains $name .Release.Name -}}
{{- .Release.Name | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}
{{- end -}}

{{- define "campusdesk.labels" -}}
app.kubernetes.io/name: {{ include "campusdesk.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
helm.sh/chart: {{ printf "%s-%s" .Chart.Name .Chart.Version }}
{{- end -}}

{{- /* The database URL is assembled once here so the Deployment and any
       migration Job cannot drift apart. */ -}}
{{- define "campusdesk.databaseUrl" -}}
postgresql+psycopg://{{ .Values.postgres.user }}:{{ .Values.postgres.password }}@{{ include "campusdesk.fullname" . }}-postgres:5432/{{ .Values.postgres.database }}
{{- end -}}
