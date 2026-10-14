package nenkin.service;

/** Action 層で共通エラーに変換するための業務 DB 例外。 */
public class NenkinDataAccessException extends RuntimeException {
    private static final long serialVersionUID = 1L;

    public NenkinDataAccessException(String message, Throwable cause) {
        super(message, cause);
    }
}
