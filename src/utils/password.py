import bcrypt


class PasswordUtil:
    """密码工具类"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        使用bcrypt加密密码
        
        Args:
            password: 明文密码
            
        Returns:
            加密后的密码字符串
        """
        salt = bcrypt.gensalt(rounds=10)
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        验证密码
        
        Args:
            plain_password: 明文密码
            hashed_password: 加密后的密码
            
        Returns:
            验证成功返回True，否则返回False
        """
        try:
            return bcrypt.checkpw(
                plain_password.encode('utf-8'),
                hashed_password.encode('utf-8')
            )
        except Exception as e:
            return False
