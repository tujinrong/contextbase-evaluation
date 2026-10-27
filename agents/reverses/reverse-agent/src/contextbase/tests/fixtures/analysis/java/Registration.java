package trial.business;
import java.util.Objects;

class 登録Service {
    private final Rules rules;
    登録Service(Rules rules) { this.rules = rules; }
    boolean save(String name) {
        if (!rules.allowed(name)) return false;
        return save(name, 1);
    }
    boolean save(String name, int count) { return count > 0; }
}

class OtherService {
    boolean save(String name) { return false; }
}
