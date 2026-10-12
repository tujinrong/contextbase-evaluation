# EXCEL出力 詳細仕様

## 概要

EXCEL出力の入力・表示・要求処理を行う。


## 処理詳細

### Excel出力実行

#### perform：nenkin/WEB-INF/src/nenkin/ExcelExportAction.java

| 順番 | 分類 | 条件・ガード | 処理・設定内容 | 根拠行 |
| --- | --- | --- | --- | --- |
| 1 | if |  | !requireStaff(request) | 14 |
| 2 | return | !requireStaff(request) | return STAFF_JSP | 14 |
| 3 | assignment | NOT (!requireStaff(request)) | ExcelViewBean bean=new ExcelViewBean() | 15 |
| 4 | assignment | NOT (!requireStaff(request)) | String text=trim(request.getParameter("BRANCH_NO")) | 15 |
| 5 | call | NOT (!requireStaff(request)) | bean.setBranchNo(text) | 15 |
| 6 | assignment | NOT (!requireStaff(request)) | Integer branch=integerOrNull(text) | 15 |
| 7 | if | NOT (!requireStaff(request)) | text.length()==0&#124;&#124;branch==null | 16 |
| 8 | call | NOT (!requireStaff(request)) / text.length()==0&#124;&#124;branch==null | bean.setMessage("店番を入力してください。") | 16 |
| 9 | call | NOT (!requireStaff(request)) / text.length()==0&#124;&#124;branch==null | setViewBean(request.getSession(),bean) | 16 |
| 10 | return | NOT (!requireStaff(request)) / text.length()==0&#124;&#124;branch==null | return EXCEL_JSP | 16 |
| 11 | if | NOT (!requireStaff(request)) / NOT (text.length()==0&#124;&#124;branch==null) | text.length()&gt;3&#124;&#124;!text.matches("[0-9]+") | 17 |
| 12 | call | NOT (!requireStaff(request)) / NOT (text.length()==0&#124;&#124;branch==null) / text.length()&gt;3&#124;&#124;!text.matches("[0-9]+") | bean.setMessage("店番は3桁以内の数字で入力してください。") | 17 |
| 13 | call | NOT (!requireStaff(request)) / NOT (text.length()==0&#124;&#124;branch==null) / text.length()&gt;3&#124;&#124;!text.matches("[0-9]+") | setViewBean(request.getSession(),bean) | 17 |
| 14 | return | NOT (!requireStaff(request)) / NOT (text.length()==0&#124;&#124;branch==null) / text.length()&gt;3&#124;&#124;!text.matches("[0-9]+") | return EXCEL_JSP | 17 |
| 15 | assignment | NOT (!requireStaff(request)) / NOT (text.length()==0&#124;&#124;branch==null) / NOT (text.length()&gt;3&#124;&#124;!text.matches("[0-9]+")) | BranchLookupItem item=ReferenceDataService.getInstance().getBranch(branch.intValue()) | 18 |
| 16 | if | NOT (!requireStaff(request)) / NOT (text.length()==0&#124;&#124;branch==null) / NOT (text.length()&gt;3&#124;&#124;!text.matches("[0-9]+")) | item!=null | 18 |
| 17 | call | NOT (!requireStaff(request)) / NOT (text.length()==0&#124;&#124;branch==null) / NOT (text.length()&gt;3&#124;&#124;!text.matches("[0-9]+")) / item!=null | bean.setBranchName(item.getBranchName()) | 18 |
| 18 | assignment | NOT (!requireStaff(request)) / NOT (text.length()==0&#124;&#124;branch==null) / NOT (text.length()&gt;3&#124;&#124;!text.matches("[0-9]+")) | PensionExcelExportResult result=PensionExcelExportService.getInstance().buildByBranch(branch.intValue()) | 19 |
| 19 | if | NOT (!requireStaff(request)) / NOT (text.length()==0&#124;&#124;branch==null) / NOT (text.length()&gt;3&#124;&#124;!text.matches("[0-9]+")) | result.getRowCount()==0 | 20 |
| 20 | call | NOT (!requireStaff(request)) / NOT (text.length()==0&#124;&#124;branch==null) / NOT (text.length()&gt;3&#124;&#124;!text.matches("[0-9]+")) / result.getRowCount()==0 | bean.setMessage("入力された店番には対象データがありません。") | 20 |
| 21 | call | NOT (!requireStaff(request)) / NOT (text.length()==0&#124;&#124;branch==null) / NOT (text.length()&gt;3&#124;&#124;!text.matches("[0-9]+")) / result.getRowCount()==0 | setViewBean(request.getSession(),bean) | 20 |
| 22 | return | NOT (!requireStaff(request)) / NOT (text.length()==0&#124;&#124;branch==null) / NOT (text.length()&gt;3&#124;&#124;!text.matches("[0-9]+")) / result.getRowCount()==0 | return EXCEL_JSP | 20 |
| 23 | call | NOT (!requireStaff(request)) / NOT (text.length()==0&#124;&#124;branch==null) / NOT (text.length()&gt;3&#124;&#124;!text.matches("[0-9]+")) / NOT (result.getRowCount()==0) | writeDownload(response,result.getFileName(),CONTENT_TYPE,result.getContent()) | 21 |
| 24 | return | NOT (!requireStaff(request)) / NOT (text.length()==0&#124;&#124;branch==null) / NOT (text.length()&gt;3&#124;&#124;!text.matches("[0-9]+")) / NOT (result.getRowCount()==0) | return "CSV" | 21 |

#### requireStaff：nenkin/WEB-INF/src/nenkin/NenkinBaseAction.java

| 順番 | 分類 | 条件・ガード | 処理・設定内容 | 根拠行 |
| --- | --- | --- | --- | --- |
| 1 | assignment |  | HttpSession session = request.getSession() | 51 |
| 2 | if |  | currentStaff(session) != null | 52 |
| 3 | call | currentStaff(session) != null | ensureCsrfToken(session) | 53 |
| 4 | return | currentStaff(session) != null | return true | 54 |
| 5 | assignment | NOT (currentStaff(session) != null) | Object value = session.getAttribute(CommonConst.SS_LOGIN_INFO_BEAN) | 57 |
| 6 | if | NOT (currentStaff(session) != null) | value instanceof LoginInfoBean &amp;&amp; ((LoginInfoBean) value).isログイン可否() | 58 |
| 7 | assignment | NOT (currentStaff(session) != null) / value instanceof LoginInfoBean &amp;&amp; ((LoginInfoBean) value).isログイン可否() | String staffNo = trim(((LoginInfoBean) value).get職員番号()) | 59 |
| 8 | if | NOT (currentStaff(session) != null) / value instanceof LoginInfoBean &amp;&amp; ((LoginInfoBean) value).isログイン可否() | staffNo.matches("[0-9]{1,8}") | 60 |
| 9 | assignment | NOT (currentStaff(session) != null) / value instanceof LoginInfoBean &amp;&amp; ((LoginInfoBean) value).isログイン可否() / staffNo.matches("[0-9]{1,8}") | StaffContext staff = ReferenceDataService.getInstance() .verifyStaff(Integer.parseInt(staffNo)) | 61 |
| 10 | if | NOT (currentStaff(session) != null) / value instanceof LoginInfoBean &amp;&amp; ((LoginInfoBean) value).isログイン可否() / staffNo.matches("[0-9]{1,8}") | staff != null | 63 |
| 11 | call | NOT (currentStaff(session) != null) / value instanceof LoginInfoBean &amp;&amp; ((LoginInfoBean) value).isログイン可否() / staffNo.matches("[0-9]{1,8}") / staff != null | session.setAttribute(STAFF_CONTEXT_KEY, staff) | 64 |
| 12 | call | NOT (currentStaff(session) != null) / value instanceof LoginInfoBean &amp;&amp; ((LoginInfoBean) value).isログイン可否() / staffNo.matches("[0-9]{1,8}") / staff != null | ensureCsrfToken(session) | 65 |
| 13 | return | NOT (currentStaff(session) != null) / value instanceof LoginInfoBean &amp;&amp; ((LoginInfoBean) value).isログイン可否() / staffNo.matches("[0-9]{1,8}") / staff != null | return true | 66 |
| 14 | call | NOT (currentStaff(session) != null) / value instanceof LoginInfoBean &amp;&amp; ((LoginInfoBean) value).isログイン可否() | session.removeAttribute(CommonConst.SS_LOGIN_INFO_BEAN) | 69 |
| 15 | call | NOT (currentStaff(session) != null) / value instanceof LoginInfoBean &amp;&amp; ((LoginInfoBean) value).isログイン可否() | session.setAttribute(CommonConst.ERROR_MSG_LIST, Collections.singletonList( "ログイン職員番号が職員名簿に存在しません。管理者に確認してください。")) | 70 |
| 16 | call | NOT (currentStaff(session) != null) / NOT (value instanceof LoginInfoBean &amp;&amp; ((LoginInfoBean) value).isログイン可否()) | session.setAttribute(CommonConst.ERROR_MSG_LIST, Collections.singletonList("ログインしてください。")) | 73 |
| 17 | call | NOT (currentStaff(session) != null) | session.removeAttribute(STAFF_CONTEXT_KEY) | 76 |
| 18 | call | NOT (currentStaff(session) != null) | session.removeAttribute(CSRF_TOKEN_KEY) | 77 |
| 19 | return | NOT (currentStaff(session) != null) | return false | 78 |

#### trim：nenkin/WEB-INF/src/nenkin/NenkinBaseAction.java

| 順番 | 分類 | 条件・ガード | 処理・設定内容 | 根拠行 |
| --- | --- | --- | --- | --- |
| 1 | return |  | return value == null ? "" : value.trim() | 119 |

#### setBranchNo：nenkin/WEB-INF/src/nenkin/bean/ExcelViewBean.java

| 順番 | 分類 | 条件・ガード | 処理・設定内容 | 根拠行 |
| --- | --- | --- | --- | --- |
| 1 | assignment |  | branchNo = value == null ? "" : value | 11 |

#### integerOrNull：nenkin/WEB-INF/src/nenkin/NenkinBaseAction.java

| 順番 | 分類 | 条件・ガード | 処理・設定内容 | 根拠行 |
| --- | --- | --- | --- | --- |
| 1 | assignment |  | String text = trim(value) | 122 |
| 2 | if |  | text.length() == 0 | 123 |
| 3 | return | text.length() == 0 | return null | 123 |
| 4 | try | NOT (text.length() == 0) |  | 124 |
| 5 | assignment | NOT (text.length() == 0) / try | int result = Integer.parseInt(text) | 124 |
| 6 | return | NOT (text.length() == 0) / try | return result &gt; 0 ? Integer.valueOf(result) : null | 124 |
| 7 | catch | NOT (text.length() == 0) | NumberFormatException e | 125 |
| 8 | return | NOT (text.length() == 0) / NumberFormatException e | return null | 125 |

#### setMessage：nenkin/WEB-INF/src/nenkin/bean/ExcelViewBean.java

| 順番 | 分類 | 条件・ガード | 処理・設定内容 | 根拠行 |
| --- | --- | --- | --- | --- |
| 1 | assignment |  | message = value == null ? "" : value | 15 |

#### setViewBean：nenkin/WEB-INF/src/nenkin/NenkinBaseAction.java

| 順番 | 分類 | 条件・ガード | 処理・設定内容 | 根拠行 |
| --- | --- | --- | --- | --- |
| 1 | call |  | session.setAttribute(CommonConst.SS_JSP_BEAN, bean) | 38 |

#### getInstance：nenkin/WEB-INF/src/nenkin/service/ReferenceDataService.java

| 順番 | 分類 | 条件・ガード | 処理・設定内容 | 根拠行 |
| --- | --- | --- | --- | --- |
| 1 | return |  | return INSTANCE | 38 |

#### getBranch：nenkin/WEB-INF/src/nenkin/service/ReferenceDataService.java

| 順番 | 分類 | 条件・ガード | 処理・設定内容 | 根拠行 |
| --- | --- | --- | --- | --- |
| 1 | assignment |  | String sql = "SELECT 店舗ｺｰﾄﾞ AS BRANCH_NO, 店名 AS BRANCH_NAME FROM " + BRANCH_TABLE + " WHERE 店舗ｺｰﾄﾞ = ?" | 185 |
| 2 | assignment |  | Connection connection = null | 187 |
| 3 | assignment |  | PreparedStatement statement = null | 188 |
| 4 | assignment |  | ResultSet results = null | 189 |
| 5 | try |  |  | 190 |
| 6 | assignment | try | connection = NenkinDataSource.openConnection() | 191 |
| 7 | assignment | try | statement = connection.prepareStatement(sql) | 192 |
| 8 | call | try | statement.setInt(1, branchNo) | 193 |
| 9 | assignment | try | results = statement.executeQuery() | 194 |
| 10 | return | try | return results.next() ? new BranchLookupItem(results.getInt("BRANCH_NO"), results.getString("BRANCH_NAME")) : null | 195 |
| 11 | catch |  | SQLException e | 197 |
| 12 | throw | SQLException e | throw failure("店舗の取得", e) | 198 |
| 13 | finally |  |  | 199 |
| 14 | call | finally | close(results) | 200 |
| 15 | call | finally | close(statement) | 201 |
| 16 | call | finally | close(connection) | 202 |

#### setBranchName：nenkin/WEB-INF/src/nenkin/bean/ExcelViewBean.java

| 順番 | 分類 | 条件・ガード | 処理・設定内容 | 根拠行 |
| --- | --- | --- | --- | --- |
| 1 | assignment |  | branchName = value == null ? "" : value | 13 |

#### getBranchName：nenkin/WEB-INF/src/nenkin/model/BranchLookupItem.java

| 順番 | 分類 | 条件・ガード | 処理・設定内容 | 根拠行 |
| --- | --- | --- | --- | --- |
| 1 | return |  | return branchName | 28 |

#### getInstance：nenkin/WEB-INF/src/nenkin/service/PensionExcelExportService.java

| 順番 | 分類 | 条件・ガード | 処理・設定内容 | 根拠行 |
| --- | --- | --- | --- | --- |
| 1 | return |  | return INSTANCE | 33 |

#### buildByBranch：nenkin/WEB-INF/src/nenkin/service/PensionExcelExportService.java

| 順番 | 分類 | 条件・ガード | 処理・設定内容 | 根拠行 |
| --- | --- | --- | --- | --- |
| 1 | assignment |  | List&lt;PensionReservation&gt; reservations = repository.listByBranch(branchNo) | 37 |
| 2 | if |  | reservations.isEmpty() | 38 |
| 3 | return | reservations.isEmpty() | return new PensionExcelExportResult("", new byte[0], 0) | 39 |
| 4 | assignment | NOT (reservations.isEmpty()) | List&lt;String&gt; headers = Arrays.asList( "顧客番号", "担\n当", "顧客氏名", "ふりがな", "性\n別", "住所", "電話番号", "生年月日", "年金種類", "裁定\n請求", "受給\n有無", "請求予定日", "予定\n年齢", "配偶者名", "配偶者\n生年月日", "予約徴求日", "備考", "６ヶ月先\n確認") | 42 |
| 5 | assignment | NOT (reservations.isEmpty()) | List&lt;Object[]&gt; rows = new ArrayList&lt;Object[]&gt;() | 47 |
| 6 | for | NOT (reservations.isEmpty()) | int i = 0; i &lt; reservations.size(); i++ | 48 |
| 7 | assignment | NOT (reservations.isEmpty()) / int i = 0; i &lt; reservations.size(); i++ | PensionReservation row = reservations.get(i) | 49 |
| 8 | call | NOT (reservations.isEmpty()) / int i = 0; i &lt; reservations.size(); i++ | rows.add(new Object[] { row.getCustomerNo(), row.getStaffCode(), row.getCustomerName(), row.getKanaName(), row.getGender(), row.getAddress(), row.getPhoneNumber(), row.getBirthDate(), row.getPensionType(), row.getClaimStatus(), row.getHasBenefit(), row.getClaimScheduledDate(), row.getPlannedAge(), row.getSpouseName(), row.getSpouseBirthDate(), row.getReservationRequestDate(), row.getNotes(), row.isSixMonthCheck() ? "確" : "" }) | 50 |
| 9 | assignment | NOT (reservations.isEmpty()) | String compactDate = DateUtil.todayIso().replace("-", "") | 60 |
| 10 | assignment | NOT (reservations.isEmpty()) | String fileName = "年金データ_" + threeDigits(branchNo) + "_" + compactDate + ".xlsx" | 61 |
| 11 | assignment | NOT (reservations.isEmpty()) | byte[] content = OpenXmlWorkbookWriter.buildWorkbook("年金ﾃﾞｰﾀ", headers, rows) | 62 |
| 12 | return | NOT (reservations.isEmpty()) | return new PensionExcelExportResult(fileName, content, rows.size()) | 63 |

#### getRowCount：nenkin/WEB-INF/src/nenkin/service/PensionExcelExportResult.java

| 順番 | 分類 | 条件・ガード | 処理・設定内容 | 根拠行 |
| --- | --- | --- | --- | --- |
| 1 | return |  | return rowCount | 27 |

#### writeDownload：nenkin/WEB-INF/src/nenkin/NenkinBaseAction.java

| 順番 | 分類 | 条件・ガード | 処理・設定内容 | 根拠行 |
| --- | --- | --- | --- | --- |
| 1 | assignment |  | String encoded = URLEncoder.encode(fileName, "UTF-8").replace("+", "%20") | 205 |
| 2 | call |  | response.reset() | 206 |
| 3 | call |  | response.setContentType(contentType) | 207 |
| 4 | assignment |  | response.setHeader("Content-Disposition", "attachment; filename=download; filename*=UTF-8''" + encoded) | 208 |
| 5 | call |  | response.setContentLength(content.length) | 209 |
| 6 | call |  | response.getOutputStream().write(content) | 210 |
| 7 | call |  | response.getOutputStream().flush() | 211 |

#### getFileName：nenkin/WEB-INF/src/nenkin/service/PensionExcelExportResult.java

| 順番 | 分類 | 条件・ガード | 処理・設定内容 | 根拠行 |
| --- | --- | --- | --- | --- |
| 1 | return |  | return fileName | 19 |

#### getContent：nenkin/WEB-INF/src/nenkin/service/PensionExcelExportResult.java

| 順番 | 分類 | 条件・ガード | 処理・設定内容 | 根拠行 |
| --- | --- | --- | --- | --- |
| 1 | return |  | return content.clone() | 23 |

#### currentStaff：nenkin/WEB-INF/src/nenkin/NenkinBaseAction.java

| 順番 | 分類 | 条件・ガード | 処理・設定内容 | 根拠行 |
| --- | --- | --- | --- | --- |
| 1 | assignment |  | Object value = session.getAttribute(STAFF_CONTEXT_KEY) | 46 |
| 2 | return |  | return value instanceof StaffContext ? (StaffContext) value : null | 47 |

#### ensureCsrfToken：nenkin/WEB-INF/src/nenkin/NenkinBaseAction.java

| 順番 | 分類 | 条件・ガード | 処理・設定内容 | 根拠行 |
| --- | --- | --- | --- | --- |
| 1 | assignment |  | Object current = session.getAttribute(CSRF_TOKEN_KEY) | 82 |
| 2 | if |  | current instanceof String &amp;&amp; ((String) current).length() &gt; 0 | 83 |
| 3 | return | current instanceof String &amp;&amp; ((String) current).length() &gt; 0 | return (String) current | 83 |
| 4 | assignment | NOT (current instanceof String &amp;&amp; ((String) current).length() &gt; 0) | String token = UUID.randomUUID().toString() | 84 |
| 5 | call | NOT (current instanceof String &amp;&amp; ((String) current).length() &gt; 0) | session.setAttribute(CSRF_TOKEN_KEY, token) | 85 |
| 6 | return | NOT (current instanceof String &amp;&amp; ((String) current).length() &gt; 0) | return token | 86 |

#### isログイン可否：n2framework/WEB-INF/src/common/bean/LoginInfoBean.java

| 順番 | 分類 | 条件・ガード | 処理・設定内容 | 根拠行 |
| --- | --- | --- | --- | --- |
| 1 | return |  | return ログイン可否 | 117 |

#### get職員番号：n2framework/WEB-INF/src/common/bean/LoginInfoBean.java

| 順番 | 分類 | 条件・ガード | 処理・設定内容 | 根拠行 |
| --- | --- | --- | --- | --- |
| 1 | return |  | return 職員番号 | 229 |

#### verifyStaff：nenkin/WEB-INF/src/nenkin/service/ReferenceDataService.java

| 順番 | 分類 | 条件・ガード | 処理・設定内容 | 根拠行 |
| --- | --- | --- | --- | --- |
| 1 | assignment |  | StaffLookupItem staff = getStaff(staffNo) | 231 |
| 2 | return |  | return staff == null ? null : new StaffContext(staff.getStaffCode(), staff.getStaffName(), staff.getBranchNo(), staff.getRoleCode()) | 232 |

#### openConnection：nenkin/WEB-INF/src/nenkin/service/NenkinDataSource.java

| 順番 | 分類 | 条件・ガード | 処理・設定内容 | 根拠行 |
| --- | --- | --- | --- | --- |
| 1 | assignment |  | DataSource dataSource = businessCached | 33 |
| 2 | if |  | dataSource == null | 34 |
| 3 | synchronized | dataSource == null | NenkinDataSource.class | 35 |
| 4 | assignment | dataSource == null / NenkinDataSource.class | dataSource = businessCached | 36 |
| 5 | if | dataSource == null / NenkinDataSource.class | dataSource == null | 37 |
| 6 | assignment | dataSource == null / NenkinDataSource.class / dataSource == null | dataSource = lookup(BUSINESS_JNDI_NAMES, "年金業務用JNDI DataSourceを取得できません。") | 38 |
| 7 | assignment | dataSource == null / NenkinDataSource.class / dataSource == null | businessCached = dataSource | 40 |
| 8 | return |  | return dataSource.getConnection() | 44 |

#### BranchLookupItem：nenkin/WEB-INF/src/nenkin/model/BranchLookupItem.java

| 順番 | 分類 | 条件・ガード | 処理・設定内容 | 根拠行 |
| --- | --- | --- | --- | --- |

#### BranchLookupItem：nenkin/WEB-INF/src/nenkin/model/BranchLookupItem.java

| 順番 | 分類 | 条件・ガード | 処理・設定内容 | 根拠行 |
| --- | --- | --- | --- | --- |
| 1 | assignment |  | this.branchNo = branchNo | 15 |
| 2 | assignment |  | this.branchName = branchName == null ? "" : branchName | 16 |

#### failure：nenkin/WEB-INF/src/nenkin/service/ReferenceDataService.java

| 順番 | 分類 | 条件・ガード | 処理・設定内容 | 根拠行 |
| --- | --- | --- | --- | --- |
| 1 | return |  | return new NenkinDataAccessException(operation + "に失敗しました。", cause) | 376 |

#### close：nenkin/WEB-INF/src/nenkin/service/ReferenceDataService.java

| 順番 | 分類 | 条件・ガード | 処理・設定内容 | 根拠行 |
| --- | --- | --- | --- | --- |
| 1 | if |  | value == null | 380 |
| 2 | return | value == null | return | 381 |
| 3 | try | NOT (value == null) |  | 383 |
| 4 | call | NOT (value == null) / try | value.close() | 384 |
| 5 | catch | NOT (value == null) | Exception e | 385 |

#### listByBranch：nenkin/WEB-INF/src/nenkin/service/PensionRepository.java

| 順番 | 分類 | 条件・ガード | 処理・設定内容 | 根拠行 |
| --- | --- | --- | --- | --- |
| 1 | assignment |  | String sql = "SELECT " + SELECT_COLUMNS + fromClause(TABLE) + " WHERE R.店番 = ? ORDER BY R.請求予定日 DESC, R.担当者コード, R.顧客番号" | 224 |
| 2 | assignment |  | List&lt;PensionReservation&gt; rows = new ArrayList&lt;PensionReservation&gt;() | 226 |
| 3 | assignment |  | Connection connection = null | 227 |
| 4 | assignment |  | PreparedStatement statement = null | 228 |
| 5 | assignment |  | ResultSet results = null | 229 |
| 6 | try |  |  | 230 |
| 7 | assignment | try | connection = NenkinDataSource.openConnection() | 231 |
| 8 | assignment | try | statement = connection.prepareStatement(sql) | 232 |
| 9 | call | try | statement.setInt(1, branchNo) | 233 |
| 10 | assignment | try | results = statement.executeQuery() | 234 |
| 11 | while | try | results.next() | 235 |
| 12 | call | try / results.next() | rows.add(readReservation(results)) | 236 |
| 13 | return | try | return rows | 238 |
| 14 | catch |  | SQLException e | 239 |
| 15 | throw | SQLException e | throw failure("店舗別年金予約の検索", e) | 240 |
| 16 | finally |  |  | 241 |
| 17 | call | finally | close(results) | 242 |
| 18 | call | finally | close(statement) | 243 |
| 19 | call | finally | close(connection) | 244 |

#### PensionExcelExportResult：nenkin/WEB-INF/src/nenkin/service/PensionExcelExportResult.java

| 順番 | 分類 | 条件・ガード | 処理・設定内容 | 根拠行 |
| --- | --- | --- | --- | --- |
| 1 | assignment |  | this.fileName = fileName == null ? "" : fileName | 13 |
| 2 | assignment |  | this.content = content == null ? new byte[0] : content.clone() | 14 |
| 3 | assignment |  | this.rowCount = rowCount | 15 |

#### get：n2framework/WEB-INF/src/webon/WebonBase.java

| 順番 | 分類 | 条件・ガード | 処理・設定内容 | 根拠行 |
| --- | --- | --- | --- | --- |
| 1 | if |  | query.containsKey(key) | 540 |
| 2 | return | query.containsKey(key) | return query.get(key) | 541 |
| 3 | return | NOT (query.containsKey(key)) | return null | 543 |

#### getCustomerNo：nenkin/WEB-INF/src/nenkin/model/PensionReservation.java

| 順番 | 分類 | 条件・ガード | 処理・設定内容 | 根拠行 |
| --- | --- | --- | --- | --- |
| 1 | return |  | return customerNo | 96 |

#### getStaffCode：nenkin/WEB-INF/src/nenkin/model/PensionReservation.java

| 順番 | 分類 | 条件・ガード | 処理・設定内容 | 根拠行 |
| --- | --- | --- | --- | --- |
| 1 | return |  | return staffCode | 104 |

#### getCustomerName：nenkin/WEB-INF/src/nenkin/model/PensionReservation.java

| 順番 | 分類 | 条件・ガード | 処理・設定内容 | 根拠行 |
| --- | --- | --- | --- | --- |
| 1 | return |  | return customerName | 112 |

#### getKanaName：nenkin/WEB-INF/src/nenkin/model/PensionReservation.java

| 順番 | 分類 | 条件・ガード | 処理・設定内容 | 根拠行 |
| --- | --- | --- | --- | --- |
| 1 | return |  | return kanaName | 120 |

#### getGender：nenkin/WEB-INF/src/nenkin/model/PensionReservation.java

| 順番 | 分類 | 条件・ガード | 処理・設定内容 | 根拠行 |
| --- | --- | --- | --- | --- |
| 1 | return |  | return gender | 128 |

#### getAddress：nenkin/WEB-INF/src/nenkin/model/PensionReservation.java

| 順番 | 分類 | 条件・ガード | 処理・設定内容 | 根拠行 |
| --- | --- | --- | --- | --- |
| 1 | return |  | return address | 136 |

#### getPhoneNumber：nenkin/WEB-INF/src/nenkin/model/PensionReservation.java

| 順番 | 分類 | 条件・ガード | 処理・設定内容 | 根拠行 |
| --- | --- | --- | --- | --- |
| 1 | return |  | return phoneNumber | 144 |

#### getBirthDate：nenkin/WEB-INF/src/nenkin/model/PensionReservation.java

| 順番 | 分類 | 条件・ガード | 処理・設定内容 | 根拠行 |
| --- | --- | --- | --- | --- |
| 1 | return |  | return birthDate | 152 |

#### getPensionType：nenkin/WEB-INF/src/nenkin/model/PensionReservation.java

| 順番 | 分類 | 条件・ガード | 処理・設定内容 | 根拠行 |
| --- | --- | --- | --- | --- |
| 1 | return |  | return pensionType | 232 |

#### getClaimStatus：nenkin/WEB-INF/src/nenkin/model/PensionReservation.java

| 順番 | 分類 | 条件・ガード | 処理・設定内容 | 根拠行 |
| --- | --- | --- | --- | --- |
| 1 | return |  | return claimStatus | 160 |

#### getHasBenefit：nenkin/WEB-INF/src/nenkin/model/PensionReservation.java

| 順番 | 分類 | 条件・ガード | 処理・設定内容 | 根拠行 |
| --- | --- | --- | --- | --- |
| 1 | return |  | return hasBenefit | 216 |

#### getClaimScheduledDate：nenkin/WEB-INF/src/nenkin/model/PensionReservation.java

| 順番 | 分類 | 条件・ガード | 処理・設定内容 | 根拠行 |
| --- | --- | --- | --- | --- |
| 1 | return |  | return claimScheduledDate | 168 |

#### getPlannedAge：nenkin/WEB-INF/src/nenkin/model/PensionReservation.java

| 順番 | 分類 | 条件・ガード | 処理・設定内容 | 根拠行 |
| --- | --- | --- | --- | --- |
| 1 | return |  | return plannedAge | 176 |

#### getSpouseName：nenkin/WEB-INF/src/nenkin/model/PensionReservation.java

| 順番 | 分類 | 条件・ガード | 処理・設定内容 | 根拠行 |
| --- | --- | --- | --- | --- |
| 1 | return |  | return spouseName | 208 |

#### getSpouseBirthDate：nenkin/WEB-INF/src/nenkin/model/PensionReservation.java

| 順番 | 分類 | 条件・ガード | 処理・設定内容 | 根拠行 |
| --- | --- | --- | --- | --- |
| 1 | return |  | return spouseBirthDate | 224 |

#### getReservationRequestDate：nenkin/WEB-INF/src/nenkin/model/PensionReservation.java

| 順番 | 分類 | 条件・ガード | 処理・設定内容 | 根拠行 |
| --- | --- | --- | --- | --- |
| 1 | return |  | return reservationRequestDate | 184 |

#### getNotes：nenkin/WEB-INF/src/nenkin/model/PensionReservation.java

| 順番 | 分類 | 条件・ガード | 処理・設定内容 | 根拠行 |
| --- | --- | --- | --- | --- |
| 1 | return |  | return notes | 200 |

#### isSixMonthCheck：nenkin/WEB-INF/src/nenkin/model/PensionReservation.java

| 順番 | 分類 | 条件・ガード | 処理・設定内容 | 根拠行 |
| --- | --- | --- | --- | --- |
| 1 | return |  | return sixMonthCheck | 280 |

#### todayIso：nenkin/WEB-INF/src/nenkin/util/DateUtil.java

| 順番 | 分類 | 条件・ガード | 処理・設定内容 | 根拠行 |
| --- | --- | --- | --- | --- |
| 1 | return |  | return new SimpleDateFormat("yyyy-MM-dd", Locale.ROOT).format(new Date()) | 115 |

#### threeDigits：nenkin/WEB-INF/src/nenkin/service/PensionExcelExportService.java

| 順番 | 分類 | 条件・ガード | 処理・設定内容 | 根拠行 |
| --- | --- | --- | --- | --- |
| 1 | assignment |  | String text = Integer.toString(value) | 67 |
| 2 | while |  | text.length() &lt; 3 | 68 |
| 3 | assignment | text.length() &lt; 3 | text = "0" + text | 69 |
| 4 | return |  | return text | 71 |

#### buildWorkbook：nenkin/WEB-INF/src/nenkin/util/OpenXmlWorkbookWriter.java

| 順番 | 分類 | 条件・ガード | 処理・設定内容 | 根拠行 |
| --- | --- | --- | --- | --- |
| 1 | return |  | return buildWorkbook(sheetName, headers, rows, null, null, 100) | 28 |

#### buildWorkbook：nenkin/WEB-INF/src/nenkin/util/OpenXmlWorkbookWriter.java

| 順番 | 分類 | 条件・ガード | 処理・設定内容 | 根拠行 |
| --- | --- | --- | --- | --- |
| 1 | if |  | headers == null &#124;&#124; headers.isEmpty() | 38 |
| 2 | throw | headers == null &#124;&#124; headers.isEmpty() | throw new IllegalArgumentException("ヘッダーは1列以上必要です。") | 39 |
| 3 | if | NOT (headers == null &#124;&#124; headers.isEmpty()) | rows == null | 41 |
| 4 | throw | NOT (headers == null &#124;&#124; headers.isEmpty()) / rows == null | throw new IllegalArgumentException("明細リストはnullにできません。") | 42 |
| 5 | assignment | NOT (headers == null &#124;&#124; headers.isEmpty()) / NOT (rows == null) | ByteArrayOutputStream output = new ByteArrayOutputStream() | 45 |
| 6 | assignment | NOT (headers == null &#124;&#124; headers.isEmpty()) / NOT (rows == null) | ZipOutputStream zip = new ZipOutputStream(output) | 46 |
| 7 | try | NOT (headers == null &#124;&#124; headers.isEmpty()) / NOT (rows == null) |  | 47 |
| 8 | call | NOT (headers == null &#124;&#124; headers.isEmpty()) / NOT (rows == null) / try | write(zip, "[Content_Types].xml", contentTypes()) | 48 |
| 9 | call | NOT (headers == null &#124;&#124; headers.isEmpty()) / NOT (rows == null) / try | write(zip, "_rels/.rels", rootRelationships()) | 49 |
| 10 | call | NOT (headers == null &#124;&#124; headers.isEmpty()) / NOT (rows == null) / try | write(zip, "xl/workbook.xml", workbookXml(sanitizeSheetName(sheetName))) | 50 |
| 11 | call | NOT (headers == null &#124;&#124; headers.isEmpty()) / NOT (rows == null) / try | write(zip, "xl/_rels/workbook.xml.rels", workbookRelationships()) | 51 |
| 12 | call | NOT (headers == null &#124;&#124; headers.isEmpty()) / NOT (rows == null) / try | write(zip, "xl/styles.xml", stylesXml()) | 52 |
| 13 | call | NOT (headers == null &#124;&#124; headers.isEmpty()) / NOT (rows == null) / try | write(zip, "xl/worksheets/sheet1.xml", sheetXml(headers, rows, leadingRows, mergedRanges, printScale)) | 53 |
| 14 | call | NOT (headers == null &#124;&#124; headers.isEmpty()) / NOT (rows == null) / try | zip.finish() | 55 |
| 15 | return | NOT (headers == null &#124;&#124; headers.isEmpty()) / NOT (rows == null) / try | return output.toByteArray() | 56 |
| 16 | catch | NOT (headers == null &#124;&#124; headers.isEmpty()) / NOT (rows == null) | IOException e | 57 |
| 17 | throw | NOT (headers == null &#124;&#124; headers.isEmpty()) / NOT (rows == null) / IOException e | throw new IllegalStateException("Excelファイルの生成に失敗しました。", e) | 58 |
| 18 | finally | NOT (headers == null &#124;&#124; headers.isEmpty()) / NOT (rows == null) |  | 59 |
| 19 | try | NOT (headers == null &#124;&#124; headers.isEmpty()) / NOT (rows == null) / finally |  | 60 |
| 20 | call | NOT (headers == null &#124;&#124; headers.isEmpty()) / NOT (rows == null) / finally / try | zip.close() | 61 |
| 21 | catch | NOT (headers == null &#124;&#124; headers.isEmpty()) / NOT (rows == null) / finally | IOException e | 62 |

#### write：nenkin/WEB-INF/src/nenkin/util/OpenXmlWorkbookWriter.java

| 順番 | 分類 | 条件・ガード | 処理・設定内容 | 根拠行 |
| --- | --- | --- | --- | --- |
| 1 | assignment |  | ZipEntry entry = new ZipEntry(path) | 293 |
| 2 | call |  | entry.setTime(0L) | 294 |
| 3 | call |  | zip.putNextEntry(entry) | 295 |
| 4 | call |  | zip.write(content.getBytes(UTF8)) | 296 |
| 5 | call |  | zip.closeEntry() | 297 |

#### getStaff：nenkin/WEB-INF/src/nenkin/service/ReferenceDataService.java

| 順番 | 分類 | 条件・ガード | 処理・設定内容 | 根拠行 |
| --- | --- | --- | --- | --- |
| 1 | assignment |  | String sql = "SELECT S.職員番号 AS STAFF_NO, S.漢字氏名 AS STAFF_NAME, " + "S.カナ氏名 AS STAFF_KANA_NAME, S.所属店番 AS BRANCH_NO, " + "S.役職コード AS ROLE_CODE FROM " + STAFF_TABLE + " S WHERE S.職員番号 = ?" | 207 |
| 2 | assignment |  | Map&lt;Integer, String&gt; branchNames = loadBranchNames() | 211 |
| 3 | assignment |  | Connection connection = null | 212 |
| 4 | assignment |  | PreparedStatement statement = null | 213 |
| 5 | assignment |  | ResultSet results = null | 214 |
| 6 | try |  |  | 215 |
| 7 | assignment | try | connection = NenkinDataSource.openStaffConnection() | 216 |
| 8 | assignment | try | statement = connection.prepareStatement(sql) | 217 |
| 9 | call | try | statement.setInt(1, staffCode) | 218 |
| 10 | assignment | try | results = statement.executeQuery() | 219 |
| 11 | return | try | return results.next() ? readStaff(results, branchNames) : null | 220 |
| 12 | catch |  | SQLException e | 221 |
| 13 | throw | SQLException e | throw failure("職員の取得", e) | 222 |
| 14 | finally |  |  | 223 |
| 15 | call | finally | close(results) | 224 |
| 16 | call | finally | close(statement) | 225 |
| 17 | call | finally | close(connection) | 226 |

#### StaffContext：nenkin/WEB-INF/src/nenkin/model/StaffContext.java

| 順番 | 分類 | 条件・ガード | 処理・設定内容 | 根拠行 |
| --- | --- | --- | --- | --- |

#### StaffContext：nenkin/WEB-INF/src/nenkin/model/StaffContext.java

| 順番 | 分類 | 条件・ガード | 処理・設定内容 | 根拠行 |
| --- | --- | --- | --- | --- |
| 1 | call |  | this(staffNo, staffName, branchNo, "") | 17 |

#### StaffContext：nenkin/WEB-INF/src/nenkin/model/StaffContext.java

| 順番 | 分類 | 条件・ガード | 処理・設定内容 | 根拠行 |
| --- | --- | --- | --- | --- |
| 1 | assignment |  | this.staffNo = staffNo | 21 |
| 2 | assignment |  | this.staffName = staffName == null ? "" : staffName | 22 |
| 3 | assignment |  | this.branchNo = branchNo | 23 |
| 4 | assignment |  | this.roleCode = roleCode == null ? "" : roleCode | 24 |

#### getStaffCode：nenkin/WEB-INF/src/nenkin/model/StaffLookupItem.java

| 順番 | 分類 | 条件・ガード | 処理・設定内容 | 根拠行 |
| --- | --- | --- | --- | --- |
| 1 | return |  | return staffCode | 38 |

#### getStaffName：nenkin/WEB-INF/src/nenkin/model/StaffLookupItem.java

| 順番 | 分類 | 条件・ガード | 処理・設定内容 | 根拠行 |
| --- | --- | --- | --- | --- |
| 1 | return |  | return staffName | 54 |

#### getBranchNo：nenkin/WEB-INF/src/nenkin/model/StaffLookupItem.java

| 順番 | 分類 | 条件・ガード | 処理・設定内容 | 根拠行 |
| --- | --- | --- | --- | --- |
| 1 | return |  | return branchNo | 70 |

#### getRoleCode：nenkin/WEB-INF/src/nenkin/model/StaffLookupItem.java

| 順番 | 分類 | 条件・ガード | 処理・設定内容 | 根拠行 |
| --- | --- | --- | --- | --- |
| 1 | return |  | return roleCode | 86 |

#### lookup：nenkin/WEB-INF/src/nenkin/service/NenkinDataSource.java

| 順番 | 分類 | 条件・ガード | 処理・設定内容 | 根拠行 |
| --- | --- | --- | --- | --- |
| 1 | assignment |  | NamingException last = null | 78 |
| 2 | for |  | int i = 0; i &lt; jndiNames.length; i++ | 79 |
| 3 | try | int i = 0; i &lt; jndiNames.length; i++ |  | 80 |
| 4 | assignment | int i = 0; i &lt; jndiNames.length; i++ / try | Object value = new InitialContext().lookup(jndiNames[i]) | 81 |
| 5 | if | int i = 0; i &lt; jndiNames.length; i++ / try | value instanceof DataSource | 82 |
| 6 | return | int i = 0; i &lt; jndiNames.length; i++ / try / value instanceof DataSource | return (DataSource) value | 83 |
| 7 | catch | int i = 0; i &lt; jndiNames.length; i++ | NamingException e | 85 |
| 8 | assignment | int i = 0; i &lt; jndiNames.length; i++ / NamingException e | last = e | 86 |
| 9 | assignment |  | SQLException failure = new SQLException(message) | 89 |
| 10 | if |  | last != null | 90 |
| 11 | call | last != null | failure.initCause(last) | 91 |
| 12 | throw |  | throw failure | 93 |

#### getConnection：n2framework/WEB-INF/src/common/base/CommonBase.java

| 順番 | 分類 | 条件・ガード | 処理・設定内容 | 根拠行 |
| --- | --- | --- | --- | --- |
| 1 | return |  | return connection | 70 |

#### NenkinDataAccessException：nenkin/WEB-INF/src/nenkin/service/NenkinDataAccessException.java

| 順番 | 分類 | 条件・ガード | 処理・設定内容 | 根拠行 |
| --- | --- | --- | --- | --- |
| 1 | call |  | super(message, cause) | 8 |

#### fromClause：nenkin/WEB-INF/src/nenkin/service/PensionRepository.java

| 順番 | 分類 | 条件・ガード | 処理・設定内容 | 根拠行 |
| --- | --- | --- | --- | --- |
| 1 | return |  | return " FROM " + table + " R" + " LEFT JOIN " + BRANCH_TABLE + " B ON R.店番 = B.店舗ｺｰﾄﾞ" + " LEFT JOIN " + GENDER_TABLE + " G ON R.性別 = G.性別ｺｰﾄﾞ" + " LEFT JOIN " + CLAIM_TABLE + " C ON R.裁定請求 = C.裁請ｺｰﾄﾞ" + " LEFT JOIN " + BENEFIT_TABLE + " H ON R.受給有無 = H.受給ｺｰﾄﾞ" + " LEFT JOIN " + PENSION_TYPE_TABLE + " P ON R.年金種類 = P.種類ｺｰﾄﾞ" | 773 |

#### readReservation：nenkin/WEB-INF/src/nenkin/service/PensionRepository.java

| 順番 | 分類 | 条件・ガード | 処理・設定内容 | 根拠行 |
| --- | --- | --- | --- | --- |
| 1 | assignment |  | PensionReservation value = new PensionReservation() | 742 |
| 2 | call |  | value.setBranchNo(nullableInteger(results, "BRANCH_NO")) | 743 |
| 3 | call |  | value.setBranchName(results.getString("BRANCH_NAME")) | 744 |
| 4 | call |  | value.setCustomerNo(nullableInteger(results, "CUSTOMER_NO")) | 745 |
| 5 | call |  | value.setStaffCode(nullableInteger(results, "STAFF_CODE")) | 746 |
| 6 | call |  | value.setCustomerName(results.getString("CUSTOMER_NAME")) | 747 |
| 7 | call |  | value.setKanaName(results.getString("KANA_NAME")) | 748 |
| 8 | call |  | value.setGender(results.getString("GENDER")) | 749 |
| 9 | call |  | value.setAddress(results.getString("ADDRESS")) | 750 |
| 10 | call |  | value.setPhoneNumber(ReferenceDataService.displayPhone(results.getString("PHONE_NUMBER"))) | 751 |
| 11 | call |  | value.setBirthDate(results.getString("BIRTH_DATE")) | 752 |
| 12 | call |  | value.setClaimStatus(results.getString("CLAIM_STATUS")) | 753 |
| 13 | call |  | value.setClaimScheduledDate(results.getString("CLAIM_SCHEDULED_DATE")) | 754 |
| 14 | call |  | value.setPlannedAge(nullableInteger(results, "PLANNED_AGE")) | 755 |
| 15 | call |  | value.setReservationRequestDate(results.getString("RESERVATION_REQUEST_DATE")) | 756 |
| 16 | call |  | value.setDataUpdateDate(results.getString("DATA_UPDATE_DATE")) | 757 |
| 17 | call |  | value.setNotes(results.getString("NOTES")) | 758 |
| 18 | call |  | value.setSpouseName(results.getString("SPOUSE_NAME")) | 759 |
| 19 | call |  | value.setHasBenefit(results.getString("HAS_BENEFIT")) | 760 |
| 20 | call |  | value.setSpouseBirthDate(results.getString("SPOUSE_BIRTH_DATE")) | 761 |
| 21 | call |  | value.setPensionType(results.getString("PENSION_TYPE")) | 762 |
| 22 | call |  | value.setNationalPension(results.getInt("NATIONAL_PENSION") != 0) | 763 |
| 23 | call |  | value.setEmployeePension(results.getInt("EMPLOYEE_PENSION") != 0) | 764 |
| 24 | call |  | value.setMutualAidPension(results.getInt("MUTUAL_AID_PENSION") != 0) | 765 |
| 25 | call |  | value.setEmployeePensionFund(results.getInt("EMPLOYEE_PENSION_FUND") != 0) | 766 |
| 26 | call |  | value.setNationalPensionFund(results.getInt("NATIONAL_PENSION_FUND") != 0) | 767 |
| 27 | call |  | value.setSixMonthCheck(results.getInt("SIX_MONTH_CHECK") != 0) | 768 |
| 28 | return |  | return value | 769 |

#### failure：nenkin/WEB-INF/src/nenkin/service/PensionRepository.java

| 順番 | 分類 | 条件・ガード | 処理・設定内容 | 根拠行 |
| --- | --- | --- | --- | --- |
| 1 | return |  | return new NenkinDataAccessException(operation + "に失敗しました。", cause) | 917 |

#### close：nenkin/WEB-INF/src/nenkin/service/PensionRepository.java

| 順番 | 分類 | 条件・ガード | 処理・設定内容 | 根拠行 |
| --- | --- | --- | --- | --- |
| 1 | if |  | value == null | 932 |
| 2 | return | value == null | return | 933 |
| 3 | try | NOT (value == null) |  | 935 |
| 4 | call | NOT (value == null) / try | value.close() | 936 |
| 5 | catch | NOT (value == null) | Exception e | 937 |

#### contentTypes：nenkin/WEB-INF/src/nenkin/util/OpenXmlWorkbookWriter.java

| 順番 | 分類 | 条件・ガード | 処理・設定内容 | 根拠行 |
| --- | --- | --- | --- | --- |
| 1 | return |  | return "&lt;?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?&gt;" + "&lt;Types xmlns=\"http://schemas.openxmlformats.org/package/2006/content-types\"&gt;" + "&lt;Default Extension=\"rels\" ContentType=\"application/vnd.openxmlformats-package.relationships+xml\"/&gt;" + "&lt;Default Extension=\"xml\" ContentType=\"application/xml\"/&gt;" + "&lt;Override PartName=\"/xl/workbook.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml\"/&gt;" + "&lt;Override PartName=\"/xl/worksheets/sheet1.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml\"/&gt;" + "&lt;Override PartName=\"/xl/styles.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml\"/&gt;" + "&lt;/Types&gt;" | 69 |

#### rootRelationships：nenkin/WEB-INF/src/nenkin/util/OpenXmlWorkbookWriter.java

| 順番 | 分類 | 条件・ガード | 処理・設定内容 | 根拠行 |
| --- | --- | --- | --- | --- |
| 1 | return |  | return "&lt;?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?&gt;" + "&lt;Relationships xmlns=\"" + RELATIONSHIP_NS + "\"&gt;" + "&lt;Relationship Id=\"rId1\" Type=\"" + OFFICE_RELATIONSHIP_NS + "/officeDocument\" Target=\"xl/workbook.xml\"/&gt;" + "&lt;/Relationships&gt;" | 80 |

#### workbookXml：nenkin/WEB-INF/src/nenkin/util/OpenXmlWorkbookWriter.java

| 順番 | 分類 | 条件・ガード | 処理・設定内容 | 根拠行 |
| --- | --- | --- | --- | --- |
| 1 | return |  | return "&lt;?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?&gt;" + "&lt;workbook xmlns=\"" + SPREADSHEET_NS + "\" xmlns:r=\"" + OFFICE_RELATIONSHIP_NS + "\"&gt;&lt;sheets&gt;&lt;sheet name=\"" + xml(sheetName) + "\" sheetId=\"1\" r:id=\"rId1\"/&gt;&lt;/sheets&gt;&lt;/workbook&gt;" | 88 |

#### sanitizeSheetName：nenkin/WEB-INF/src/nenkin/util/OpenXmlWorkbookWriter.java

| 順番 | 分類 | 条件・ガード | 処理・設定内容 | 根拠行 |
| --- | --- | --- | --- | --- |
| 1 | assignment |  | String name = value == null &#124;&#124; value.trim().length() == 0 ? "Sheet1" : value.trim() | 262 |
| 2 | assignment |  | name = name.replaceAll("[\\\\/\\?\\*\\[\\]:]", "_") | 263 |
| 3 | if |  | name.length() &gt; 31 | 264 |
| 4 | assignment | name.length() &gt; 31 | name = name.substring(0, 31) | 265 |
| 5 | return |  | return name | 267 |

#### workbookRelationships：nenkin/WEB-INF/src/nenkin/util/OpenXmlWorkbookWriter.java

| 順番 | 分類 | 条件・ガード | 処理・設定内容 | 根拠行 |
| --- | --- | --- | --- | --- |
| 1 | return |  | return "&lt;?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?&gt;" + "&lt;Relationships xmlns=\"" + RELATIONSHIP_NS + "\"&gt;" + "&lt;Relationship Id=\"rId1\" Type=\"" + OFFICE_RELATIONSHIP_NS + "/worksheet\" Target=\"worksheets/sheet1.xml\"/&gt;" + "&lt;Relationship Id=\"rId2\" Type=\"" + OFFICE_RELATIONSHIP_NS + "/styles\" Target=\"styles.xml\"/&gt;" + "&lt;/Relationships&gt;" | 95 |

#### stylesXml：nenkin/WEB-INF/src/nenkin/util/OpenXmlWorkbookWriter.java

| 順番 | 分類 | 条件・ガード | 処理・設定内容 | 根拠行 |
| --- | --- | --- | --- | --- |
| 1 | return |  | return "&lt;?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?&gt;" + "&lt;styleSheet xmlns=\"" + SPREADSHEET_NS + "\"&gt;" + "&lt;fonts count=\"4\"&gt;&lt;font&gt;&lt;sz val=\"10\"/&gt;&lt;name val=\"メイリオ\"/&gt;&lt;/font&gt;" + "&lt;font&gt;&lt;b/&gt;&lt;sz val=\"10\"/&gt;&lt;name val=\"メイリオ\"/&gt;&lt;/font&gt;" + "&lt;font&gt;&lt;b/&gt;&lt;sz val=\"22\"/&gt;&lt;name val=\"メイリオ\"/&gt;&lt;/font&gt;" + "&lt;font&gt;&lt;sz val=\"16\"/&gt;&lt;name val=\"メイリオ\"/&gt;&lt;/font&gt;&lt;/fonts&gt;" + "&lt;fills count=\"3\"&gt;&lt;fill&gt;&lt;patternFill patternType=\"none\"/&gt;&lt;/fill&gt;" + "&lt;fill&gt;&lt;patternFill patternType=\"gray125\"/&gt;&lt;/fill&gt;" + "&lt;fill&gt;&lt;patternFill patternType=\"solid\"&gt;&lt;fgColor rgb=\"FFFFFF96\"/&gt;" + "&lt;bgColor indexed=\"64\"/&gt;&lt;/patternFill&gt;&lt;/fill&gt;&lt;/fills&gt;" + "&lt;borders count=\"2\"&gt;&lt;border&gt;&lt;left/&gt;&lt;right/&gt;&lt;top/&gt;&lt;bottom/&gt;&lt;diagonal/&gt;&lt;/border&gt;" + "&lt;border&gt;&lt;left style=\"thin\"/&gt;&lt;right style=\"thin\"/&gt;&lt;top style=\"thin\"/&gt;" + "&lt;bottom style=\"thin\"/&gt;&lt;diagonal/&gt;&lt;/border&gt;&lt;/borders&gt;" + "&lt;cellStyleXfs count=\"1\"&gt;&lt;xf numFmtId=\"0\" fontId=\"0\" fillId=\"0\" borderId=\"0\"/&gt;&lt;/cellStyleXfs&gt;" + "&lt;cellXfs count=\"5\"&gt;" + "&lt;xf numFmtId=\"0\" fontId=\"0\" fillId=\"0\" borderId=\"1\" xfId=\"0\" applyBorder=\"1\"/&gt;" + "&lt;xf numFmtId=\"0\" fontId=\"1\" fillId=\"2\" borderId=\"1\" xfId=\"0\" applyFont=\"1\" applyFill=\"1\" applyBorder=\"1\" applyAlignment=\"1\"&gt;&lt;alignment horizontal=\"center\" vertical=\"center\" wrapText=\"1\"/&gt;&lt;/xf&gt;" + "&lt;xf numFmtId=\"0\" fontId=\"0\" fillId=\"0\" borderId=\"1\" xfId=\"0\" applyBorder=\"1\" applyAlignment=\"1\"&gt;&lt;alignment horizontal=\"right\" vertical=\"top\"/&gt;&lt;/xf&gt;" + "&lt;xf numFmtId=\"0\" fontId=\"2\" fillId=\"0\" borderId=\"0\" xfId=\"0\" applyFont=\"1\" applyAlignment=\"1\"&gt;&lt;alignment horizontal=\"center\" vertical=\"center\"/&gt;&lt;/xf&gt;" + "&lt;xf numFmtId=\"0\" fontId=\"3\" fillId=\"0\" borderId=\"0\" xfId=\"0\" applyFont=\"1\" applyAlignment=\"1\"&gt;&lt;alignment horizontal=\"center\" vertical=\"center\"/&gt;&lt;/xf&gt;" + "&lt;/cellXfs&gt;&lt;cellStyles count=\"1\"&gt;&lt;cellStyle name=\"Normal\" xfId=\"0\" builtinId=\"0\"/&gt;&lt;/cellStyles&gt;" + "&lt;/styleSheet&gt;" | 105 |

#### sheetXml：nenkin/WEB-INF/src/nenkin/util/OpenXmlWorkbookWriter.java

| 順番 | 分類 | 条件・ガード | 処理・設定内容 | 根拠行 |
| --- | --- | --- | --- | --- |
| 1 | assignment |  | StringBuilder xml = new StringBuilder(4096 + rows.size() * headers.size() * 40) | 131 |
| 2 | assignment |  | int leadingCount = leadingRows == null ? 0 : leadingRows.size() | 132 |
| 3 | assignment |  | int headerRow = leadingCount + 1 | 133 |
| 4 | assignment |  | int lastRow = rows.size() + headerRow | 134 |
| 5 | assignment |  | String lastColumn = columnName(headers.size()) | 135 |
| 6 | assignment |  | xml.append("&lt;?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?&gt;") | 136 |
| 7 | assignment |  | xml.append("&lt;worksheet xmlns=\"").append(SPREADSHEET_NS).append("\"&gt;") | 137 |
| 8 | assignment |  | xml.append("&lt;dimension ref=\"A1:").append(lastColumn).append(lastRow).append("\"/&gt;") | 138 |
| 9 | assignment |  | xml.append("&lt;sheetViews&gt;&lt;sheetView workbookViewId=\"0\"&gt;&lt;pane ySplit=\"") .append(headerRow).append("\" topLeftCell=\"A").append(headerRow + 1) .append("\" activePane=\"bottomLeft\" state=\"frozen\"/&gt;&lt;/sheetView&gt;&lt;/sheetViews&gt;") | 139 |
| 10 | call |  | appendColumns(xml, headers, rows) | 142 |
| 11 | call |  | xml.append("&lt;sheetData&gt;") | 143 |
| 12 | if |  | leadingRows != null | 144 |
| 13 | for | leadingRows != null | int rowIndex = 0; rowIndex &lt; leadingRows.size(); rowIndex++ | 145 |
| 14 | assignment | leadingRows != null / int rowIndex = 0; rowIndex &lt; leadingRows.size(); rowIndex++ | int excelRow = rowIndex + 1 | 146 |
| 15 | assignment | leadingRows != null / int rowIndex = 0; rowIndex &lt; leadingRows.size(); rowIndex++ | Object[] row = leadingRows.get(rowIndex) | 147 |
| 16 | assignment | leadingRows != null / int rowIndex = 0; rowIndex &lt; leadingRows.size(); rowIndex++ | xml.append("&lt;row r=\"").append(excelRow).append("\"") | 148 |
| 17 | if | leadingRows != null / int rowIndex = 0; rowIndex &lt; leadingRows.size(); rowIndex++ | excelRow == 1 | 149 |
| 18 | assignment | leadingRows != null / int rowIndex = 0; rowIndex &lt; leadingRows.size(); rowIndex++ / excelRow == 1 | xml.append(" ht=\"28\" customHeight=\"1\"") | 150 |
| 19 | call | leadingRows != null / int rowIndex = 0; rowIndex &lt; leadingRows.size(); rowIndex++ | xml.append('&gt;') | 152 |
| 20 | if | leadingRows != null / int rowIndex = 0; rowIndex &lt; leadingRows.size(); rowIndex++ | row != null | 153 |
| 21 | for | leadingRows != null / int rowIndex = 0; rowIndex &lt; leadingRows.size(); rowIndex++ / row != null | int column = 0; column &lt; Math.min(headers.size(), row.length); column++ | 154 |
| 22 | assignment | leadingRows != null / int rowIndex = 0; rowIndex &lt; leadingRows.size(); rowIndex++ / row != null / int column = 0; column &lt; Math.min(headers.size(), row.length); column++ | Object value = row[column] | 155 |
| 23 | if | leadingRows != null / int rowIndex = 0; rowIndex &lt; leadingRows.size(); rowIndex++ / row != null / int column = 0; column &lt; Math.min(headers.size(), row.length); column++ | value != null | 156 |
| 24 | call | leadingRows != null / int rowIndex = 0; rowIndex &lt; leadingRows.size(); rowIndex++ / row != null / int column = 0; column &lt; Math.min(headers.size(), row.length); column++ / value != null | appendTextCell(xml, columnName(column + 1) + excelRow, String.valueOf(value), excelRow == 1 ? 3 : 4) | 157 |
| 25 | call | leadingRows != null / int rowIndex = 0; rowIndex &lt; leadingRows.size(); rowIndex++ | xml.append("&lt;/row&gt;") | 162 |
| 26 | assignment |  | xml.append("&lt;row r=\"").append(headerRow) .append("\" ht=\"45\" customHeight=\"1\"&gt;") | 165 |
| 27 | for |  | int column = 0; column &lt; headers.size(); column++ | 167 |
| 28 | call | int column = 0; column &lt; headers.size(); column++ | appendTextCell(xml, columnName(column + 1) + headerRow, headers.get(column), 1) | 168 |
| 29 | call |  | xml.append("&lt;/row&gt;") | 170 |
| 30 | for |  | int rowIndex = 0; rowIndex &lt; rows.size(); rowIndex++ | 172 |
| 31 | assignment | int rowIndex = 0; rowIndex &lt; rows.size(); rowIndex++ | int excelRow = rowIndex + headerRow + 1 | 173 |
| 32 | assignment | int rowIndex = 0; rowIndex &lt; rows.size(); rowIndex++ | Object[] row = rows.get(rowIndex) | 174 |
| 33 | assignment | int rowIndex = 0; rowIndex &lt; rows.size(); rowIndex++ | xml.append("&lt;row r=\"").append(excelRow).append("\"&gt;") | 175 |
| 34 | for | int rowIndex = 0; rowIndex &lt; rows.size(); rowIndex++ | int column = 0; column &lt; headers.size(); column++ | 176 |
| 35 | assignment | int rowIndex = 0; rowIndex &lt; rows.size(); rowIndex++ / int column = 0; column &lt; headers.size(); column++ | Object value = row != null &amp;&amp; column &lt; row.length ? row[column] : null | 177 |
| 36 | assignment | int rowIndex = 0; rowIndex &lt; rows.size(); rowIndex++ / int column = 0; column &lt; headers.size(); column++ | String reference = columnName(column + 1) + excelRow | 178 |
| 37 | if | int rowIndex = 0; rowIndex &lt; rows.size(); rowIndex++ / int column = 0; column &lt; headers.size(); column++ | value instanceof Number | 179 |
| 38 | call | int rowIndex = 0; rowIndex &lt; rows.size(); rowIndex++ / int column = 0; column &lt; headers.size(); column++ / value instanceof Number | appendNumberCell(xml, reference, (Number) value) | 180 |
| 39 | call | int rowIndex = 0; rowIndex &lt; rows.size(); rowIndex++ / int column = 0; column &lt; headers.size(); column++ / NOT (value instanceof Number) | appendTextCell(xml, reference, value == null ? "" : String.valueOf(value), 0) | 182 |
| 40 | call | int rowIndex = 0; rowIndex &lt; rows.size(); rowIndex++ | xml.append("&lt;/row&gt;") | 185 |
| 41 | assignment |  | xml.append("&lt;/sheetData&gt;&lt;autoFilter ref=\"A").append(headerRow).append(':') .append(lastColumn).append(lastRow).append("\"/&gt;") | 188 |
| 42 | if |  | mergedRanges != null &amp;&amp; !mergedRanges.isEmpty() | 190 |
| 43 | assignment | mergedRanges != null &amp;&amp; !mergedRanges.isEmpty() | xml.append("&lt;mergeCells count=\"").append(mergedRanges.size()).append("\"&gt;") | 191 |
| 44 | for | mergedRanges != null &amp;&amp; !mergedRanges.isEmpty() | int i = 0; i &lt; mergedRanges.size(); i++ | 192 |
| 45 | assignment | mergedRanges != null &amp;&amp; !mergedRanges.isEmpty() / int i = 0; i &lt; mergedRanges.size(); i++ | xml.append("&lt;mergeCell ref=\"").append(xml(mergedRanges.get(i))).append("\"/&gt;") | 193 |
| 46 | call | mergedRanges != null &amp;&amp; !mergedRanges.isEmpty() | xml.append("&lt;/mergeCells&gt;") | 195 |
| 47 | assignment |  | xml.append("&lt;printOptions horizontalCentered=\"1\"/&gt;") .append("&lt;pageMargins left=\"0\" right=\"0\" top=\"0.3937\" bottom=\"0.3937\" header=\"0.1181\" footer=\"0.1181\"/&gt;") .append("&lt;pageSetup paperSize=\"9\" orientation=\"portrait\" scale=\"") .append(Math.max(10, Math.min(400, printScale))).append("\"/&gt;") .append("&lt;/worksheet&gt;") | 197 |
| 48 | return |  | return xml.toString() | 202 |

#### setTime：nenkin/WEB-INF/src/nenkin/service/PensionRepository.java

| 順番 | 分類 | 条件・ガード | 処理・設定内容 | 根拠行 |
| --- | --- | --- | --- | --- |
| 1 | assignment |  | String time = text(value) | 829 |
| 2 | if |  | time.length() &lt; 8 | 830 |
| 3 | call | time.length() &lt; 8 | statement.setNull(index, Types.TIME) | 831 |
| 4 | call | NOT (time.length() &lt; 8) | statement.setTime(index, java.sql.Time.valueOf(time.substring(0, 8))) | 833 |

#### loadBranchNames：nenkin/WEB-INF/src/nenkin/service/ReferenceDataService.java

| 順番 | 分類 | 条件・ガード | 処理・設定内容 | 根拠行 |
| --- | --- | --- | --- | --- |
| 1 | assignment |  | Map&lt;Integer, String&gt; branchNames = new HashMap&lt;Integer, String&gt;() | 290 |
| 2 | assignment |  | String sql = "SELECT 店舗ｺｰﾄﾞ AS BRANCH_NO, 店名 AS BRANCH_NAME FROM " + BRANCH_TABLE | 291 |
| 3 | assignment |  | Connection connection = null | 293 |
| 4 | assignment |  | PreparedStatement statement = null | 294 |
| 5 | assignment |  | ResultSet results = null | 295 |
| 6 | try |  |  | 296 |
| 7 | assignment | try | connection = NenkinDataSource.openConnection() | 297 |
| 8 | assignment | try | statement = connection.prepareStatement(sql) | 298 |
| 9 | assignment | try | results = statement.executeQuery() | 299 |
| 10 | while | try | results.next() | 300 |
| 11 | call | try / results.next() | branchNames.put(Integer.valueOf(results.getInt("BRANCH_NO")), results.getString("BRANCH_NAME")) | 301 |
| 12 | return | try | return branchNames | 304 |
| 13 | catch |  | SQLException e | 305 |
| 14 | throw | SQLException e | throw failure("店舗名の取得", e) | 306 |
| 15 | finally |  |  | 307 |
| 16 | call | finally | close(results) | 308 |
| 17 | call | finally | close(statement) | 309 |
| 18 | call | finally | close(connection) | 310 |

#### openStaffConnection：nenkin/WEB-INF/src/nenkin/service/NenkinDataSource.java

| 順番 | 分類 | 条件・ガード | 処理・設定内容 | 根拠行 |
| --- | --- | --- | --- | --- |
| 1 | assignment |  | DataSource dataSource = staffCached | 48 |
| 2 | if |  | dataSource == null | 49 |
| 3 | synchronized | dataSource == null | NenkinDataSource.class | 50 |
| 4 | assignment | dataSource == null / NenkinDataSource.class | dataSource = staffCached | 51 |
| 5 | if | dataSource == null / NenkinDataSource.class | dataSource == null | 52 |
| 6 | assignment | dataSource == null / NenkinDataSource.class / dataSource == null | dataSource = lookup(STAFF_JNDI_NAMES, "N2職員名簿用JNDI DataSourceを取得できません。") | 53 |
| 7 | assignment | dataSource == null / NenkinDataSource.class / dataSource == null | staffCached = dataSource | 55 |
| 8 | return |  | return dataSource.getConnection() | 59 |

#### readStaff：nenkin/WEB-INF/src/nenkin/service/ReferenceDataService.java

| 順番 | 分類 | 条件・ガード | 処理・設定内容 | 根拠行 |
| --- | --- | --- | --- | --- |
| 1 | assignment |  | int branchNo = results.getInt("BRANCH_NO") | 316 |
| 2 | assignment |  | String branchName = branchNames.get(Integer.valueOf(branchNo)) | 317 |
| 3 | return |  | return new StaffLookupItem(results.getInt("STAFF_NO"), results.getString("STAFF_NAME"), results.getString("STAFF_KANA_NAME"), branchNo, branchName == null ? "" : branchName, results.getString("ROLE_CODE")) | 318 |

#### PensionReservation：nenkin/WEB-INF/src/nenkin/model/PensionReservation.java

| 順番 | 分類 | 条件・ガード | 処理・設定内容 | 根拠行 |
| --- | --- | --- | --- | --- |

### Excel出力画面表示

#### perform：nenkin/WEB-INF/src/nenkin/ExcelViewAction.java

| 順番 | 分類 | 条件・ガード | 処理・設定内容 | 根拠行 |
| --- | --- | --- | --- | --- |
| 1 | if |  | !requireStaff(request) | 3 |
| 2 | return | !requireStaff(request) | return STAFF_JSP | 3 |
| 3 | call | NOT (!requireStaff(request)) | setViewBean(request.getSession(),new ExcelViewBean()) | 3 |
| 4 | return | NOT (!requireStaff(request)) | return EXCEL_JSP | 3 |

#### requireStaff：nenkin/WEB-INF/src/nenkin/NenkinBaseAction.java

| 順番 | 分類 | 条件・ガード | 処理・設定内容 | 根拠行 |
| --- | --- | --- | --- | --- |
| 1 | assignment |  | HttpSession session = request.getSession() | 51 |
| 2 | if |  | currentStaff(session) != null | 52 |
| 3 | call | currentStaff(session) != null | ensureCsrfToken(session) | 53 |
| 4 | return | currentStaff(session) != null | return true | 54 |
| 5 | assignment | NOT (currentStaff(session) != null) | Object value = session.getAttribute(CommonConst.SS_LOGIN_INFO_BEAN) | 57 |
| 6 | if | NOT (currentStaff(session) != null) | value instanceof LoginInfoBean &amp;&amp; ((LoginInfoBean) value).isログイン可否() | 58 |
| 7 | assignment | NOT (currentStaff(session) != null) / value instanceof LoginInfoBean &amp;&amp; ((LoginInfoBean) value).isログイン可否() | String staffNo = trim(((LoginInfoBean) value).get職員番号()) | 59 |
| 8 | if | NOT (currentStaff(session) != null) / value instanceof LoginInfoBean &amp;&amp; ((LoginInfoBean) value).isログイン可否() | staffNo.matches("[0-9]{1,8}") | 60 |
| 9 | assignment | NOT (currentStaff(session) != null) / value instanceof LoginInfoBean &amp;&amp; ((LoginInfoBean) value).isログイン可否() / staffNo.matches("[0-9]{1,8}") | StaffContext staff = ReferenceDataService.getInstance() .verifyStaff(Integer.parseInt(staffNo)) | 61 |
| 10 | if | NOT (currentStaff(session) != null) / value instanceof LoginInfoBean &amp;&amp; ((LoginInfoBean) value).isログイン可否() / staffNo.matches("[0-9]{1,8}") | staff != null | 63 |
| 11 | call | NOT (currentStaff(session) != null) / value instanceof LoginInfoBean &amp;&amp; ((LoginInfoBean) value).isログイン可否() / staffNo.matches("[0-9]{1,8}") / staff != null | session.setAttribute(STAFF_CONTEXT_KEY, staff) | 64 |
| 12 | call | NOT (currentStaff(session) != null) / value instanceof LoginInfoBean &amp;&amp; ((LoginInfoBean) value).isログイン可否() / staffNo.matches("[0-9]{1,8}") / staff != null | ensureCsrfToken(session) | 65 |
| 13 | return | NOT (currentStaff(session) != null) / value instanceof LoginInfoBean &amp;&amp; ((LoginInfoBean) value).isログイン可否() / staffNo.matches("[0-9]{1,8}") / staff != null | return true | 66 |
| 14 | call | NOT (currentStaff(session) != null) / value instanceof LoginInfoBean &amp;&amp; ((LoginInfoBean) value).isログイン可否() | session.removeAttribute(CommonConst.SS_LOGIN_INFO_BEAN) | 69 |
| 15 | call | NOT (currentStaff(session) != null) / value instanceof LoginInfoBean &amp;&amp; ((LoginInfoBean) value).isログイン可否() | session.setAttribute(CommonConst.ERROR_MSG_LIST, Collections.singletonList( "ログイン職員番号が職員名簿に存在しません。管理者に確認してください。")) | 70 |
| 16 | call | NOT (currentStaff(session) != null) / NOT (value instanceof LoginInfoBean &amp;&amp; ((LoginInfoBean) value).isログイン可否()) | session.setAttribute(CommonConst.ERROR_MSG_LIST, Collections.singletonList("ログインしてください。")) | 73 |
| 17 | call | NOT (currentStaff(session) != null) | session.removeAttribute(STAFF_CONTEXT_KEY) | 76 |
| 18 | call | NOT (currentStaff(session) != null) | session.removeAttribute(CSRF_TOKEN_KEY) | 77 |
| 19 | return | NOT (currentStaff(session) != null) | return false | 78 |

#### setViewBean：nenkin/WEB-INF/src/nenkin/NenkinBaseAction.java

| 順番 | 分類 | 条件・ガード | 処理・設定内容 | 根拠行 |
| --- | --- | --- | --- | --- |
| 1 | call |  | session.setAttribute(CommonConst.SS_JSP_BEAN, bean) | 38 |

#### currentStaff：nenkin/WEB-INF/src/nenkin/NenkinBaseAction.java

| 順番 | 分類 | 条件・ガード | 処理・設定内容 | 根拠行 |
| --- | --- | --- | --- | --- |
| 1 | assignment |  | Object value = session.getAttribute(STAFF_CONTEXT_KEY) | 46 |
| 2 | return |  | return value instanceof StaffContext ? (StaffContext) value : null | 47 |

#### ensureCsrfToken：nenkin/WEB-INF/src/nenkin/NenkinBaseAction.java

| 順番 | 分類 | 条件・ガード | 処理・設定内容 | 根拠行 |
| --- | --- | --- | --- | --- |
| 1 | assignment |  | Object current = session.getAttribute(CSRF_TOKEN_KEY) | 82 |
| 2 | if |  | current instanceof String &amp;&amp; ((String) current).length() &gt; 0 | 83 |
| 3 | return | current instanceof String &amp;&amp; ((String) current).length() &gt; 0 | return (String) current | 83 |
| 4 | assignment | NOT (current instanceof String &amp;&amp; ((String) current).length() &gt; 0) | String token = UUID.randomUUID().toString() | 84 |
| 5 | call | NOT (current instanceof String &amp;&amp; ((String) current).length() &gt; 0) | session.setAttribute(CSRF_TOKEN_KEY, token) | 85 |
| 6 | return | NOT (current instanceof String &amp;&amp; ((String) current).length() &gt; 0) | return token | 86 |

#### isログイン可否：n2framework/WEB-INF/src/common/bean/LoginInfoBean.java

| 順番 | 分類 | 条件・ガード | 処理・設定内容 | 根拠行 |
| --- | --- | --- | --- | --- |
| 1 | return |  | return ログイン可否 | 117 |

#### trim：nenkin/WEB-INF/src/nenkin/NenkinBaseAction.java

| 順番 | 分類 | 条件・ガード | 処理・設定内容 | 根拠行 |
| --- | --- | --- | --- | --- |
| 1 | return |  | return value == null ? "" : value.trim() | 119 |

#### get職員番号：n2framework/WEB-INF/src/common/bean/LoginInfoBean.java

| 順番 | 分類 | 条件・ガード | 処理・設定内容 | 根拠行 |
| --- | --- | --- | --- | --- |
| 1 | return |  | return 職員番号 | 229 |

#### getInstance：nenkin/WEB-INF/src/nenkin/service/ReferenceDataService.java

| 順番 | 分類 | 条件・ガード | 処理・設定内容 | 根拠行 |
| --- | --- | --- | --- | --- |
| 1 | return |  | return INSTANCE | 38 |

#### verifyStaff：nenkin/WEB-INF/src/nenkin/service/ReferenceDataService.java

| 順番 | 分類 | 条件・ガード | 処理・設定内容 | 根拠行 |
| --- | --- | --- | --- | --- |
| 1 | assignment |  | StaffLookupItem staff = getStaff(staffNo) | 231 |
| 2 | return |  | return staff == null ? null : new StaffContext(staff.getStaffCode(), staff.getStaffName(), staff.getBranchNo(), staff.getRoleCode()) | 232 |

#### getStaff：nenkin/WEB-INF/src/nenkin/service/ReferenceDataService.java

| 順番 | 分類 | 条件・ガード | 処理・設定内容 | 根拠行 |
| --- | --- | --- | --- | --- |
| 1 | assignment |  | String sql = "SELECT S.職員番号 AS STAFF_NO, S.漢字氏名 AS STAFF_NAME, " + "S.カナ氏名 AS STAFF_KANA_NAME, S.所属店番 AS BRANCH_NO, " + "S.役職コード AS ROLE_CODE FROM " + STAFF_TABLE + " S WHERE S.職員番号 = ?" | 207 |
| 2 | assignment |  | Map&lt;Integer, String&gt; branchNames = loadBranchNames() | 211 |
| 3 | assignment |  | Connection connection = null | 212 |
| 4 | assignment |  | PreparedStatement statement = null | 213 |
| 5 | assignment |  | ResultSet results = null | 214 |
| 6 | try |  |  | 215 |
| 7 | assignment | try | connection = NenkinDataSource.openStaffConnection() | 216 |
| 8 | assignment | try | statement = connection.prepareStatement(sql) | 217 |
| 9 | call | try | statement.setInt(1, staffCode) | 218 |
| 10 | assignment | try | results = statement.executeQuery() | 219 |
| 11 | return | try | return results.next() ? readStaff(results, branchNames) : null | 220 |
| 12 | catch |  | SQLException e | 221 |
| 13 | throw | SQLException e | throw failure("職員の取得", e) | 222 |
| 14 | finally |  |  | 223 |
| 15 | call | finally | close(results) | 224 |
| 16 | call | finally | close(statement) | 225 |
| 17 | call | finally | close(connection) | 226 |

#### StaffContext：nenkin/WEB-INF/src/nenkin/model/StaffContext.java

| 順番 | 分類 | 条件・ガード | 処理・設定内容 | 根拠行 |
| --- | --- | --- | --- | --- |

#### StaffContext：nenkin/WEB-INF/src/nenkin/model/StaffContext.java

| 順番 | 分類 | 条件・ガード | 処理・設定内容 | 根拠行 |
| --- | --- | --- | --- | --- |
| 1 | call |  | this(staffNo, staffName, branchNo, "") | 17 |

#### StaffContext：nenkin/WEB-INF/src/nenkin/model/StaffContext.java

| 順番 | 分類 | 条件・ガード | 処理・設定内容 | 根拠行 |
| --- | --- | --- | --- | --- |
| 1 | assignment |  | this.staffNo = staffNo | 21 |
| 2 | assignment |  | this.staffName = staffName == null ? "" : staffName | 22 |
| 3 | assignment |  | this.branchNo = branchNo | 23 |
| 4 | assignment |  | this.roleCode = roleCode == null ? "" : roleCode | 24 |

#### getStaffCode：nenkin/WEB-INF/src/nenkin/model/StaffLookupItem.java

| 順番 | 分類 | 条件・ガード | 処理・設定内容 | 根拠行 |
| --- | --- | --- | --- | --- |
| 1 | return |  | return staffCode | 38 |

#### getStaffName：nenkin/WEB-INF/src/nenkin/model/StaffLookupItem.java

| 順番 | 分類 | 条件・ガード | 処理・設定内容 | 根拠行 |
| --- | --- | --- | --- | --- |
| 1 | return |  | return staffName | 54 |

#### getBranchNo：nenkin/WEB-INF/src/nenkin/model/StaffLookupItem.java

| 順番 | 分類 | 条件・ガード | 処理・設定内容 | 根拠行 |
| --- | --- | --- | --- | --- |
| 1 | return |  | return branchNo | 70 |

#### getRoleCode：nenkin/WEB-INF/src/nenkin/model/StaffLookupItem.java

| 順番 | 分類 | 条件・ガード | 処理・設定内容 | 根拠行 |
| --- | --- | --- | --- | --- |
| 1 | return |  | return roleCode | 86 |

#### loadBranchNames：nenkin/WEB-INF/src/nenkin/service/ReferenceDataService.java

| 順番 | 分類 | 条件・ガード | 処理・設定内容 | 根拠行 |
| --- | --- | --- | --- | --- |
| 1 | assignment |  | Map&lt;Integer, String&gt; branchNames = new HashMap&lt;Integer, String&gt;() | 290 |
| 2 | assignment |  | String sql = "SELECT 店舗ｺｰﾄﾞ AS BRANCH_NO, 店名 AS BRANCH_NAME FROM " + BRANCH_TABLE | 291 |
| 3 | assignment |  | Connection connection = null | 293 |
| 4 | assignment |  | PreparedStatement statement = null | 294 |
| 5 | assignment |  | ResultSet results = null | 295 |
| 6 | try |  |  | 296 |
| 7 | assignment | try | connection = NenkinDataSource.openConnection() | 297 |
| 8 | assignment | try | statement = connection.prepareStatement(sql) | 298 |
| 9 | assignment | try | results = statement.executeQuery() | 299 |
| 10 | while | try | results.next() | 300 |
| 11 | call | try / results.next() | branchNames.put(Integer.valueOf(results.getInt("BRANCH_NO")), results.getString("BRANCH_NAME")) | 301 |
| 12 | return | try | return branchNames | 304 |
| 13 | catch |  | SQLException e | 305 |
| 14 | throw | SQLException e | throw failure("店舗名の取得", e) | 306 |
| 15 | finally |  |  | 307 |
| 16 | call | finally | close(results) | 308 |
| 17 | call | finally | close(statement) | 309 |
| 18 | call | finally | close(connection) | 310 |

#### openStaffConnection：nenkin/WEB-INF/src/nenkin/service/NenkinDataSource.java

| 順番 | 分類 | 条件・ガード | 処理・設定内容 | 根拠行 |
| --- | --- | --- | --- | --- |
| 1 | assignment |  | DataSource dataSource = staffCached | 48 |
| 2 | if |  | dataSource == null | 49 |
| 3 | synchronized | dataSource == null | NenkinDataSource.class | 50 |
| 4 | assignment | dataSource == null / NenkinDataSource.class | dataSource = staffCached | 51 |
| 5 | if | dataSource == null / NenkinDataSource.class | dataSource == null | 52 |
| 6 | assignment | dataSource == null / NenkinDataSource.class / dataSource == null | dataSource = lookup(STAFF_JNDI_NAMES, "N2職員名簿用JNDI DataSourceを取得できません。") | 53 |
| 7 | assignment | dataSource == null / NenkinDataSource.class / dataSource == null | staffCached = dataSource | 55 |
| 8 | return |  | return dataSource.getConnection() | 59 |

#### readStaff：nenkin/WEB-INF/src/nenkin/service/ReferenceDataService.java

| 順番 | 分類 | 条件・ガード | 処理・設定内容 | 根拠行 |
| --- | --- | --- | --- | --- |
| 1 | assignment |  | int branchNo = results.getInt("BRANCH_NO") | 316 |
| 2 | assignment |  | String branchName = branchNames.get(Integer.valueOf(branchNo)) | 317 |
| 3 | return |  | return new StaffLookupItem(results.getInt("STAFF_NO"), results.getString("STAFF_NAME"), results.getString("STAFF_KANA_NAME"), branchNo, branchName == null ? "" : branchName, results.getString("ROLE_CODE")) | 318 |

#### failure：nenkin/WEB-INF/src/nenkin/service/ReferenceDataService.java

| 順番 | 分類 | 条件・ガード | 処理・設定内容 | 根拠行 |
| --- | --- | --- | --- | --- |
| 1 | return |  | return new NenkinDataAccessException(operation + "に失敗しました。", cause) | 376 |

#### close：nenkin/WEB-INF/src/nenkin/service/ReferenceDataService.java

| 順番 | 分類 | 条件・ガード | 処理・設定内容 | 根拠行 |
| --- | --- | --- | --- | --- |
| 1 | if |  | value == null | 380 |
| 2 | return | value == null | return | 381 |
| 3 | try | NOT (value == null) |  | 383 |
| 4 | call | NOT (value == null) / try | value.close() | 384 |
| 5 | catch | NOT (value == null) | Exception e | 385 |

#### openConnection：nenkin/WEB-INF/src/nenkin/service/NenkinDataSource.java

| 順番 | 分類 | 条件・ガード | 処理・設定内容 | 根拠行 |
| --- | --- | --- | --- | --- |
| 1 | assignment |  | DataSource dataSource = businessCached | 33 |
| 2 | if |  | dataSource == null | 34 |
| 3 | synchronized | dataSource == null | NenkinDataSource.class | 35 |
| 4 | assignment | dataSource == null / NenkinDataSource.class | dataSource = businessCached | 36 |
| 5 | if | dataSource == null / NenkinDataSource.class | dataSource == null | 37 |
| 6 | assignment | dataSource == null / NenkinDataSource.class / dataSource == null | dataSource = lookup(BUSINESS_JNDI_NAMES, "年金業務用JNDI DataSourceを取得できません。") | 38 |
| 7 | assignment | dataSource == null / NenkinDataSource.class / dataSource == null | businessCached = dataSource | 40 |
| 8 | return |  | return dataSource.getConnection() | 44 |

#### put：n2framework/WEB-INF/src/webon/WebonBase.java

| 順番 | 分類 | 条件・ガード | 処理・設定内容 | 根拠行 |
| --- | --- | --- | --- | --- |
| 1 | call |  | query.put(key, value) | 520 |
| 2 | if |  | key.equals("原店番号") | 525 |
| 3 | if | key.equals("原店番号") | query.get("原店番号").equals(query.get("取引店舗コード")) | 526 |
| 4 | assignment | key.equals("原店番号") / query.get("原店番号").equals(query.get("取引店舗コード")) | FWLog.debug(getClass(), "原店番号=取引店舗コードのため、原店番号の設定をはずします。") | 527 |
| 5 | call | key.equals("原店番号") / query.get("原店番号").equals(query.get("取引店舗コード")) | query.put("原店番号","") | 528 |

#### put：n2framework/WEB-INF/src/webon/WebonBase.java

| 順番 | 分類 | 条件・ガード | 処理・設定内容 | 根拠行 |
| --- | --- | --- | --- | --- |
| 1 | statement |  | String key | 553 |
| 2 | statement |  | String value | 554 |
| 3 | assignment |  | Set&lt;String&gt; ks = map.keySet() | 555 |
| 4 | for |  | Iterator&lt;String&gt; ksIt = ks.iterator(); ksIt.hasNext(); | 556 |
| 5 | assignment | Iterator&lt;String&gt; ksIt = ks.iterator(); ksIt.hasNext(); | key=ksIt.next() | 557 |
| 6 | assignment | Iterator&lt;String&gt; ksIt = ks.iterator(); ksIt.hasNext(); | value=map.get(key) | 558 |
| 7 | call | Iterator&lt;String&gt; ksIt = ks.iterator(); ksIt.hasNext(); | this.put(key,value) | 559 |

#### lookup：nenkin/WEB-INF/src/nenkin/service/NenkinDataSource.java

| 順番 | 分類 | 条件・ガード | 処理・設定内容 | 根拠行 |
| --- | --- | --- | --- | --- |
| 1 | assignment |  | NamingException last = null | 78 |
| 2 | for |  | int i = 0; i &lt; jndiNames.length; i++ | 79 |
| 3 | try | int i = 0; i &lt; jndiNames.length; i++ |  | 80 |
| 4 | assignment | int i = 0; i &lt; jndiNames.length; i++ / try | Object value = new InitialContext().lookup(jndiNames[i]) | 81 |
| 5 | if | int i = 0; i &lt; jndiNames.length; i++ / try | value instanceof DataSource | 82 |
| 6 | return | int i = 0; i &lt; jndiNames.length; i++ / try / value instanceof DataSource | return (DataSource) value | 83 |
| 7 | catch | int i = 0; i &lt; jndiNames.length; i++ | NamingException e | 85 |
| 8 | assignment | int i = 0; i &lt; jndiNames.length; i++ / NamingException e | last = e | 86 |
| 9 | assignment |  | SQLException failure = new SQLException(message) | 89 |
| 10 | if |  | last != null | 90 |
| 11 | call | last != null | failure.initCause(last) | 91 |
| 12 | throw |  | throw failure | 93 |

#### getConnection：n2framework/WEB-INF/src/common/base/CommonBase.java

| 順番 | 分類 | 条件・ガード | 処理・設定内容 | 根拠行 |
| --- | --- | --- | --- | --- |
| 1 | return |  | return connection | 70 |

#### get：n2framework/WEB-INF/src/webon/WebonBase.java

| 順番 | 分類 | 条件・ガード | 処理・設定内容 | 根拠行 |
| --- | --- | --- | --- | --- |
| 1 | if |  | query.containsKey(key) | 540 |
| 2 | return | query.containsKey(key) | return query.get(key) | 541 |
| 3 | return | NOT (query.containsKey(key)) | return null | 543 |

#### StaffLookupItem：nenkin/WEB-INF/src/nenkin/model/StaffLookupItem.java

| 順番 | 分類 | 条件・ガード | 処理・設定内容 | 根拠行 |
| --- | --- | --- | --- | --- |

#### StaffLookupItem：nenkin/WEB-INF/src/nenkin/model/StaffLookupItem.java

| 順番 | 分類 | 条件・ガード | 処理・設定内容 | 根拠行 |
| --- | --- | --- | --- | --- |
| 1 | call |  | this(staffCode, staffName, "", branchNo, branchName, "") | 19 |

#### StaffLookupItem：nenkin/WEB-INF/src/nenkin/model/StaffLookupItem.java

| 順番 | 分類 | 条件・ガード | 処理・設定内容 | 根拠行 |
| --- | --- | --- | --- | --- |
| 1 | call |  | this(staffCode, staffName, staffKanaName, branchNo, branchName, "") | 24 |

#### StaffLookupItem：nenkin/WEB-INF/src/nenkin/model/StaffLookupItem.java

| 順番 | 分類 | 条件・ガード | 処理・設定内容 | 根拠行 |
| --- | --- | --- | --- | --- |
| 1 | assignment |  | this.staffCode = staffCode | 29 |
| 2 | assignment |  | this.staffName = staffName == null ? "" : staffName | 30 |
| 3 | assignment |  | this.staffKanaName = staffKanaName == null ? "" : staffKanaName | 31 |
| 4 | assignment |  | this.branchNo = branchNo | 32 |
| 5 | assignment |  | this.branchName = branchName == null ? "" : branchName | 33 |
| 6 | assignment |  | this.roleCode = roleCode == null ? "" : roleCode | 34 |

#### NenkinDataAccessException：nenkin/WEB-INF/src/nenkin/service/NenkinDataAccessException.java

| 順番 | 分類 | 条件・ガード | 処理・設定内容 | 根拠行 |
| --- | --- | --- | --- | --- |
| 1 | call |  | super(message, cause) | 8 |

#### debug：n2framework/WEB-INF/src/common/FWLog.java

| 順番 | 分類 | 条件・ガード | 処理・設定内容 | 根拠行 |
| --- | --- | --- | --- | --- |
| 1 | call |  | logger.debug(msg) | 50 |

#### debug：n2framework/WEB-INF/src/common/FWLog.java

| 順番 | 分類 | 条件・ガード | 処理・設定内容 | 根拠行 |
| --- | --- | --- | --- | --- |
| 1 | call |  | logger.debug(cls.getName() + DEVIDE_MSG + msg) | 60 |

### データ関連

| 種別 | 対象 | 操作 | 根拠 |
| --- | --- | --- | --- |
| session | 職員情報等（セッション） | read | requireStaff |
| session | 職員情報等（セッション） | read | requireStaff |
| session | 職員情報等（セッション） | read | requireStaff |
| session | 職員情報等（セッション） | read | requireStaff |
| session | 職員情報等（セッション） | read | requireStaff |
| session | 職員情報等（セッション） | read | requireStaff |
| session | 職員情報等（セッション） | read | requireStaff |
| session | 職員情報等（セッション） | read | setViewBean |
| session | 職員情報等（セッション） | read | currentStaff |
| session | 職員情報等（セッション） | read | ensureCsrfToken |
| session | 職員情報等（セッション） | read | ensureCsrfToken |
| database | NAVI.ＵＳパス管理ステータス | C | literal_sql |
| database | DB2.ＵＪ科目 | R | literal_sql |
| database | DB2.ＵＪ科目 | R | literal_sql |
| database | NAVI.ＵＭ機能マスタ | R | literal_sql |
| database | NAVI.ＵＪ機能マスタ | R | literal_sql |
| database | NAVI.ＵＭオンラインＯＰマスタ | R | literal_sql |
| database | NAVI.ＵＪ稼動店舗管理マスタ | R | literal_sql |
| database | NAVI.ＵＪ稼動店舗管理マスタ | R | literal_sql |
| database | NAVI.ＵＪ稼動店舗管理マスタ | R | literal_sql |
| database | NAVI.ＵＭパス管理マスタ | R | literal_sql |
| database | NAVI.ＵＳパス管理ステータス | R | literal_sql |
| database | NAVI.ＵＳパス管理ステータス | R | literal_sql |
| database | NAVI.ＵＳパス管理ステータス | U | literal_sql |
| database | NAVI.ＵＳパス管理ステータス | U | literal_sql |
| database | 年金1_LK | C | literal_sql |
| database | 年金＿削除明細 | C | literal_sql |
| database | 年金1_LK | U | literal_sql |
| database | N2_SIGHT.Ｂ顧客基本表 | R | literal_sql |
| database | 年金1_LK | R | literal_sql |
| database | 店名テーブル | R | literal_sql |
| database | 性別テーブル | R | literal_sql |
| database | 裁定請求テーブル | R | literal_sql |
| database | 受給有無テーブル | R | literal_sql |
| database | 年金種類テーブル | R | literal_sql |
| database | 年金1_LK | R | literal_sql |
| database | 店名テーブル | R | literal_sql |
| database | 性別テーブル | R | literal_sql |
| database | 裁定請求テーブル | R | literal_sql |
| database | 受給有無テーブル | R | literal_sql |
| database | 年金種類テーブル | R | literal_sql |
| database | 年金1_LK | D | literal_sql |
| database | 年金1_LK | R | literal_sql |
| database | 年金＿削除明細 | R | literal_sql |
| database | 年金＿削除明細 | D | literal_sql |
| database | 店名テーブル | R | literal_sql |
| database | 年金種類テーブル | R | literal_sql |
| database | 年金1_LK | R | literal_sql |
| database | 年金1_LK | R | literal_sql |
| database | 店名テーブル | R | literal_sql |
| database | 性別テーブル | R | literal_sql |
| database | 裁定請求テーブル | R | literal_sql |
| database | 受給有無テーブル | R | literal_sql |
| database | 年金種類テーブル | R | literal_sql |
| database | 年金1_LK | C | literal_sql |
| database | 年金1_LK | U | literal_sql |
| database | 年金＿削除明細 | C | literal_sql |
| database | 店名テーブル | R | literal_sql |
| database | DB2.Ｕ職員名簿表 | R | literal_sql |
| database | 店名テーブル | R | literal_sql |
| database | 年金1_LK | read | listByBranch@223 |
| database | 店名テーブル | read | listByBranch@223 |
| database | 性別テーブル | read | listByBranch@223 |
| database | 裁定請求テーブル | read | listByBranch@223 |
| database | 受給有無テーブル | read | listByBranch@223 |
| database | 年金種類テーブル | read | listByBranch@223 |
| database | 店名テーブル | read | getBranch@184 |
| database | DB2.Ｕ職員名簿表 | read | getStaff@206 |
| database | 店名テーブル | read | loadBranchNames@289 |


## 検証シナリオ

| ID | 入力・条件 | 期待結果 |
| --- | --- | --- |
| SCR-015-S01 | 各イベントの分岐条件を満たす入力 | 詳細仕様の分岐ごとの応答・状態変更を照合する（静的抽出による期待仕様候補） |

