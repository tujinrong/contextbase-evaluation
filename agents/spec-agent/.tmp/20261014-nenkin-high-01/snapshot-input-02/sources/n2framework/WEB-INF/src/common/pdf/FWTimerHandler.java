/*
 * 作成日: 2007/05/24
 *
 */
package common.pdf;

/*
 * FWTimerHandler.java
 */

/**
 * FWTimerHandler インターフェイス
 * 
 * タイマー機能で呼び出されるハンドラ
 * 
 * @date	H22.9.3		青木・浅見		センター集約対応なし
 */
public interface FWTimerHandler {
	/**
	 * 設定された時間になったときに呼び出されるメソッドです。
	 */
	public void handleTimer(Object userInfo);
}

