// COM-Vue_CSharpAPI, SCR-STU-001/002. Decimal strings preserve all 64-bit IDs/versions.
export type EntityId = string;
export interface BirthDateInput { era: string; year: string; month: string; day: string }
export interface StudentSaveRequest {
  studentNo: string; studentName: string; studentNameKana: string; birthDateInput: BirthDateInput;
  genderCode: string; postalCode: string; prefectureCode: string; addressLine1: string; addressLine2: string | null;
  phoneNumber: string | null; emailAddress: string | null; admissionDate: string; enrollmentStatusCode: string;
  enrollmentEndDate: string | null; classId: EntityId | null; emergencyContactName: string | null;
  relationshipCode: string | null; emergencyPhoneNumber: string | null; remarks: string | null;
  schoolYear: number | null; gradeCode: string | null; expectedVersion: EntityId | null;
  duplicateToken: string | null; operationReason: string | null; returnContextId: string | null;
}
export interface SearchCriteria { studentNo: string; name: string; kana: string; schoolYear: number | null; gradeCode: string | null; classId: EntityId | null; unassignedOnly: boolean; statusCodes: string[]; prefectureCode: string | null; phoneNumber: string; admissionFrom: string | null; admissionTo: string | null }
export interface CodeItem { categoryId: string; value: string; name: string; selectable: boolean; note?: string }
export interface ClassItem { classId: EntityId; schoolYear: number; gradeCode: string; gradeName: string; classCode: string; className: string; selectable: boolean; note: string; occupancy: number | null; capacity: number | null }
export interface Lookups { codes: CodeItem[]; classes: ClassItem[]; years: number[] }
export interface Permissions { read: boolean; create: boolean; update: boolean; delete: boolean; maintain: boolean }
export interface StudentListItem { studentId: EntityId; studentNo: string; studentName: string; studentNameKana: string; birthDateWareki: string; schoolYear: number | null; gradeName: string; classCode: string; className: string; enrollmentName: string; addressDisplay: string; phoneNumber: string | null; updatedAt: string }
export interface ApiError { outcome: string; messageId: string; message: string; fieldErrors: Record<string, string[]>; correlationId: string; retryBySearch: boolean }
export interface SearchResult { outcome: 'unsearched' | 'found' | 'empty' | 'tooMany'; totalCount: number | null; items: StudentListItem[]; page: number; pageSize: number; sortKey: string; sortDirection: string; searchedAt: string | null; contextId: string; contextRevision: string; criteria: SearchCriteria }
export interface Bootstrap extends Lookups { csrfToken: string; user: string; permissions: Permissions; businessDate: string; schoolYear: number; contextId: string; contextRevision: string }
export interface StudentEditData extends Lookups { studentId: EntityId | null; form: StudentSaveRequest; updatedAt: string | null; updatedBy: string | null; permissions: Permissions }
export interface Candidate { studentId: EntityId; studentNo: string; studentName: string; birthDate: string; birthDateWareki: string; classLabel: string }
export interface SaveResult extends Partial<ApiError> { outcome: string; studentId?: EntityId; rowVersion?: EntityId; duplicateToken?: string; candidateCount?: number; candidates?: Candidate[] }
export const initialCriteria = (): SearchCriteria => ({ studentNo: '', name: '', kana: '', schoolYear: null, gradeCode: null, classId: null, unassignedOnly: false, statusCodes: ['01','02'], prefectureCode: null, phoneNumber: '', admissionFrom: null, admissionTo: null });
export const clone = <T>(value: T): T => JSON.parse(JSON.stringify(value)) as T;
